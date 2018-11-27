import json
import logging

import requests
from blog.models import Entry, Tag, Photo
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now
from django.views import View

log = logging.getLogger("micropub")


class BadRequest(Exception):
    pass


class MicropubBase(View):
    """
    Handles auth and a few odds and ends (csrf exemption) for all descending Micropub views.
    """

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

    def authorize(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header and "access_token" in request.POST:
            auth_header = "Bearer " + request.POST["access_token"]

        if not auth_header:
            log.info("permission denied: no auth token")
            return HttpResponse(status=401)

        # Since indieauth requires rel=me links back to the site (i.e. link to
        # my site in my github profile), if we're on staging aiuth won't work.
        # So, alow a bypass of auth in STAGING/DEBUG.
        if settings.STAGING or settings.DEBUG:
            bypass = getattr(settings, "INDIEAUTH_BYPASS_SECRET", "")
            if bypass == auth_header.replace("Bearer ", ""):
                return {"me": "https://jacobian.org/"}

        response = requests.get(
            "https://tokens.indieauth.com/token",
            headers={"Authorization": auth_header, "Accept": "application/json"},
        )

        if response.status_code not in (200, 201):
            log.info(
                "permission denied: token endpoint returned %s", response.status_code
            )
            return HttpResponse(status=401)

        indieauth = response.json()
        if indieauth["me"].rstrip("/") != "https://jacobian.org":
            log.info("permission denied me=%s", indieauth["me"])
            return HttpResponse(status=401)

        if "create" not in indieauth["scope"]:
            log.info(
                "permission denied, lacking create scope, scope=%s", indieauth["scope"]
            )
            return HttpResponse(status=401)

        log.info("authorized me=%s", indieauth["me"])
        return indieauth


class Micropub(MicropubBase):
    http_method_names = ["get", "post"]

    def get(self, request):
        """
        GET /micropub --> returns various config info
        """
        log.debug("get micropub q=%s", request.GET.dict())
        return JsonResponse(
            {"media-endpoint": request.build_absolute_uri(reverse("micropub_media"))}
        )

    def post(self, request):
        auth = self.authorize(request)
        if isinstance(auth, HttpResponse):
            return auth

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

        created = now()

        title = h_entry["properties"].get("name", [""])[0]
        slug = h_entry["properties"].get("mp-slug", [slugify(title)])[0][:50]
        if "mp-slug" in h_entry["properties"]:
            slug = h_entry["properties"]["mp-slug"][0]
        elif title:
            slug = slugify(title)
        else:
            slug = created.strftime("%H%I%S")

        entry = Entry.objects.create(
            created=created,
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


class MicropubMedia(MicropubBase):
    http_method_names = ["post"]

    def post(self, request):
        auth = self.authorize(request)
        if isinstance(auth, HttpResponse):
            return auth

        if "file" not in request.FILES:
            raise BadRequest("invalid request: no files uploaded")

        # Really this could be a file of any type... so using a Photo
        # model will need to go once this becomes more general purpose.
        photo = Photo.objects.create(
            photo=request.FILES["file"], slug=slugify(request.FILES["file"].name)
        )

        response = HttpResponse(status=201)
        response["Location"] = photo.photo.url
        return response

