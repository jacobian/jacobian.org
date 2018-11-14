import requests
import json
import logging
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from django.utils.text import Truncator, slugify
from blog.models import Entry

log = logging.getLogger("micropub")


class Micropub(View):
    http_method_names = ["get", "post"]

    def get(self, request):
        """
        GET /micropub --> returns various config info
        """
        log.debug("get micropub q=%s", request.GET.dict())
        return JsonResponse({})

    def post(self, request):
        self.authorize(request)

        if request.content_type == "application/json":
            payload = json.loads(request.body)
        elif request.content_type == "application/x-www-form-urlencoded":
            return HttpResponseBadRequest("can't handle form data (yet)")
        else:
            return HttpResponseBadRequest(
                f"can't handle content-type: {request.content_type}"
            )

        log.debug("payload=%s", payload)

        if "action" in payload:
            return HttpResponseBadRequest(f"can't handle anything other than create")

        post_type = payload.get("type", ["h-entry"])[0]
        if post_type != "h-entry":
            return HttpResponseBadRequest(f"only supports h-entry, not {post_type}")

        # FIXME: This is a sketch; should be substantially more robust
        # Why are these lists?
        body = payload["properties"]["content"][0]["html"]
        if "name" in payload["properties"]:
            title = payload["properties"]["name"][0]
        else:
            title = Truncator(title).words(15, truncate=" …")

        slug = payload["properties"].get("mp-slug", [slugify(title)])[0][:50]

        e = Entry.objects.create(
            created=now(),
            title=title,
            body=body,
            slug=slug,
            metadata={"micropub_payload": payload},
        )

        response = HttpResponse(status=201)
        response["Location"] = request.build_absolute_uri(e.get_absolute_url())
        return response

    def authorize(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header and "access_token" in request.POST:
            auth_header = "Bearer " + request.POST["access_token"]

        if not auth_header:
            log.info("permission denied: no auth token")
            raise PermissionDenied()

        response = requests.get(
            "https://tokens.indieauth.com/token",
            headers={"Authorization": auth_header, "Accept": "application/json"},
        )

        if response.status_code not in (200, 201):
            log.info(
                "permission denied: token endpoint returned %s", response.status_code
            )
            raise PermissionDenied()

        indieauth = response.json()
        if indieauth["me"].rstrip("/") != "https://jacobian.org":
            log.info("permission denied me=%s", indieauth["me"])
            raise PermissionDenied()

        if "create" not in indieauth["scope"]:
            log.info(
                "permission denied, lacking create scope, scope=%s", indieauth["scope"]
            )
            raise PermissionDenied()

        log.info("authorized me=%s", indieauth["me"])
        return indieauth

    @classmethod
    def as_view(klass):
        view = super().as_view()
        view.csrf_exempt = True
        return view
