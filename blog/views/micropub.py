import requests
import json
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from django.utils.text import Truncator, slugify
from blog.models import Entry


class Micropub(View):
    http_method_names = ["get", "post"]

    def get(self, request):
        """
        GET /micropub --> returns various config info
        """
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
            raise PermissionDenied("no auth token")

        response = requests.get(
            "https://tokens.indieauth.com/token",
            headers={"Authorization": auth_header, "Accept": "application/json"},
        )

        if response.status_code not in (200, 201):
            raise PermissionDenied(f"token endpoint returned {response.status_code}")

        indieauth = response.json()
        if indieauth["me"].rstrip("/") != "https://jacobian.org":
            raise PermissionDenied("not me")

        if "create" not in indieauth["scope"]:
            raise PermissionDenied("lacking create scope")

        return indieauth

    @classmethod
    def as_view(klass):
        view = super().as_view()
        view.csrf_exempt = True
        return view
