import pytest
import json
from django.http import QueryDict
from blog.views import micropub as micropub_views
from blog.models import Entry

H_ENTRY = {
    "type": ["h-entry"],
    "properties": {"content": ["hi there"], "mp-slug": ["hi"], "name": "hi"},
}
H_ENTRY_NO_NAME = {
    "type": ["h-entry"],
    "properties": {"content": ["hi there"], "mp-slug": ["hi"]},
}
H_ENTRY_WITH_TAGS = {
    "type": ["h-entry"],
    "properties": {
        "content": ["this has tags"],
        "mp-slug": ["hi"],
        "name": "hi",
        "category": ["tag1", "tag2"],
    },
}


def test_micropub_get(rf):
    request = rf.get("/micropub")
    view = micropub_views.Micropub.as_view()
    response = view(request)
    assert response.content == b"{}"


def test_micropub_decode_formdat():
    post = QueryDict("h=entry&content=hi+there&slug=hi&tags[]=a&tags[]=b&tags[]=c")
    v = micropub_views.Micropub()
    decoded = v.decode_formdata(post)
    assert decoded["type"] == ["h-entry"]
    assert decoded["properties"]["content"] == ["hi there"]
    assert decoded["properties"]["slug"] == ["hi"]
    assert decoded["properties"]["tags"] == ["a", "b", "c"]


def test_parse_payload_json(rf):
    request = rf.post(
        "/payload", content_type="application/json", data=json.dumps(H_ENTRY)
    )
    view = micropub_views.Micropub()
    payload = view.parse_payload(request)
    assert payload == H_ENTRY


@pytest.mark.django_db
def test_construct_entry(rf):
    request = rf.post(
        "/payload", content_type="application/json", data=json.dumps(H_ENTRY)
    )
    view = micropub_views.Micropub()
    payload = view.parse_payload(request)
    entry = view.construct_entry(payload)
    assert entry.title == H_ENTRY["properties"]["name"][0]
    assert entry.slug == H_ENTRY["properties"]["mp-slug"][0]
    assert entry.body == "<p>" + H_ENTRY["properties"]["content"][0] + "</p>"


@pytest.mark.django_db
def test_construct_entry_no_title(rf):
    request = rf.post(
        "/payload", content_type="application/json", data=json.dumps(H_ENTRY_NO_NAME)
    )
    view = micropub_views.Micropub()
    payload = view.parse_payload(request)
    entry = view.construct_entry(payload)
    assert entry.title == ""
    assert entry.slug == H_ENTRY_NO_NAME["properties"]["mp-slug"][0]
    assert entry.body == "<p>" + H_ENTRY_NO_NAME["properties"]["content"][0] + "</p>"


class NoAuthMicropub(micropub_views.Micropub):
    """
    Stub out authorize() for testing
    """

    def authorize(self, request):
        return {"me": "https://jacobian.org/"}


@pytest.mark.django_db
def test_micropub_post(rf):
    request = rf.post(
        "/micropub", content_type="application/json", data=json.dumps(H_ENTRY)
    )
    view = NoAuthMicropub.as_view()
    response = view(request)

    assert response.status_code == 201

    entry = Entry.objects.get(slug=H_ENTRY["properties"]["mp-slug"][0])
    assert entry.title == H_ENTRY["properties"]["name"][0]
    assert entry.body == "<p>" + H_ENTRY["properties"]["content"][0] + "</p>"

    assert response["Location"] == request.build_absolute_uri(entry.get_absolute_url())


@pytest.mark.django_db
def test_micropub_post_with_tags(rf):
    request = rf.post(
        "/micropub", content_type="application/json", data=json.dumps(H_ENTRY_WITH_TAGS)
    )
    NoAuthMicropub.as_view()(request)

    entry = Entry.objects.get(slug=H_ENTRY_WITH_TAGS["properties"]["mp-slug"][0])
    assert {t.tag for t in entry.tags.all()} == set(
        H_ENTRY_WITH_TAGS["properties"]["category"]
    )

