import requests
import json
import logging
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from django.utils.text import Truncator, slugify
from django.utils.html import strip_tags
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
            log.debug("decoding formdata post=%s", request.POST.dict())
            payload = self.decode_formdata(request.POST)
        else:
            log.debug("invalid content-type=%s", request.content_type)
            return HttpResponseBadRequest()

        log.debug("payload=%s", payload)

        if "action" in payload:
            return HttpResponseBadRequest(f"can't handle anything other than create")

        post_type = payload.get("type", ["h-entry"])[0]
        if post_type != "h-entry":
            return HttpResponseBadRequest(f"only supports h-entry, not {post_type}")

        # FIXME: This is a sketch; should be substantially more robust

        content = payload["properties"]["content"][0]
        if type(content) == str:
            body = f"<p>{content}</p>"
        elif "html" in content:
            body = content["html"]
        else:
            log.debug("don't know how to handle content=%s", content)
            return HttpResponseBadRequest()

        if "name" in payload["properties"]:
            title = payload["properties"]["name"][0]
        else:
            title = Truncator(strip_tags(body)).words(15, truncate=" …")

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

    def decode_formdata(self, post):
        """
        Decode form-encoded microformat into a microformat dict
        """
        mf = {
            "type": ["h-" + post.get("h", "entry")],
            "properties": {"content": [post.get("content", "")]},
        }

        for key in post:
            if key in ("h", "content", "access_token"):
                continue
            mf["properties"][key.replace("[]", "")] = post.getlist(key)

        return mf

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
