from django.http import QueryDict
from blog.views import micropub as micropub_views


def test_micropub_decode_post():
    post = QueryDict("h=entry&content=hi+there&slug=hi&tags[]=a&tags[]=b&tags[]=c")
    v = micropub_views.Micropub()
    decoded = v.decode_formdata(post)
    assert decoded["type"] == ["h-entry"]
    assert decoded["properties"]["content"] == ["hi there"]
    assert decoded["properties"]["slug"] == ["hi"]
    assert decoded["properties"]["tags"] == ["a", "b", "c"]
