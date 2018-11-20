import json
import logging

import requests
from blog.models import Entry, Tag
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify
from django.utils.timezone import now
from django.views import View


class BadRequest(Exception):
    pass


log = logging.getLogger("micropub")


class Micropub(View):
    http_method_names = ["get", "post"]

    @classmethod
    def as_view(klass):
        view = super().as_view()
        view.csrf_exempt = True
        return view

    def dispatch(self, request):
        """Wrap dispatch() so that we can `raise BadRequest`"""
        try:
            return super().dispatch(request)
        except BadRequest as e:
            log.debug("bad request", *e.args)
            return HttpResponseBadRequest(e.args[0])

    def get(self, request):
        """
        GET /micropub --> returns various config info
        """
        log.debug("get micropub q=%s", request.GET.dict())
        return JsonResponse({})

    def post(self, request):
        self.authorize(request)

        payload = self.parse_payload(request)
        log.debug("payload=%s", payload)

        if "action" in payload:
            raise BadRequest("can't handle actions yet")

        post_type = payload.get("type", ["h-entry"])[0]
        if post_type != "h-entry":
            raise BadRequest(f"only supports h-entry, not {post_type}")

        entry = self.construct_entry(payload)

        response = HttpResponse(status=201)
        response["Location"] = request.build_absolute_uri(entry.get_absolute_url())
        return response

    def parse_payload(self, request):
        """
        Parse out the micropub payload from the request, which can be
        either JSON (easy) or form-data (a bit harder).

        TODO: multipart/form-data, which is for file uploads.
        """
        if request.content_type == "application/json":
            return json.loads(request.body)
        elif request.content_type == "application/x-www-form-urlencoded":
            log.debug("decoding formdata post=%s", request.POST.dict())
            return self.decode_formdata(request.POST)
        else:
            raise BadRequest("invalid content-type=%s", request.content_type)

    def decode_formdata(self, post):
        """
        Decode form-encoded micropub into a microformat dict
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

    def construct_entry(self, h_entry):
        """
        Turn an h-entry document into an Entry object.

        Doesn't save it, mostly to make testing easier.

        FIXME: I wrote this just by looking at what various clients send;
        I should read the spec and see what all else is possible. e.g. can
        bodies be markdown? other formats?
        """

        content = h_entry["properties"]["content"][0]
        if type(content) == str:
            body = f"<p>{content}</p>"
        elif "html" in content:
            body = content["html"]
        else:
            log.debug("don't know how to handle content=%s", content)
            return HttpResponseBadRequest()

        if "name" in h_entry["properties"]:
            title = h_entry["properties"]["name"][0]
        else:
            title = Truncator(strip_tags(body)).words(15, truncate=" …")

        slug = h_entry["properties"].get("mp-slug", [slugify(title)])[0][:50]

        entry = Entry.objects.create(
            created=now(),
            title=title,
            body=body,
            slug=slug,
            metadata={"h_entry": h_entry},
        )

        tags = [
            Tag.objects.get_or_create(tag=tag)[0]
            for tag in h_entry["properties"].get("category", [])
        ]
        entry.tags.set(tags)

        return entry

    def authorize(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header and "access_token" in request.POST:
            auth_header = "Bearer " + request.POST["access_token"]

        if not auth_header:
            log.info("permission denied: no auth token")
            raise PermissionDenied()

        # Since indieauth requires rel=me links back to the site (i.e. link to
        # my site in my github profile), if we're on staging aiuth won't work.
        # So, alow a bypass of auth in STAGING/DEBUG.
        if settings.STAGING or settings.DEBUG:
            if getattr(settings, 'INDIEAUTH_BYPASS_SECRET', '') == auth_header.replace('Bearer ', ''):
                return {"me": "https://jacobian.org/"}

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
