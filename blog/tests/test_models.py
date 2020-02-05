import pytest
from blog.models import Entry


def test_entry_no_title():
    e = Entry(body="xyzfoo")
    assert str(e) == "xyzfoo"


# Needs transaction=True to trigger the post-save signal (see signals.py), which
# was failing, see issue #5
@pytest.mark.django_db(transaction=True)
def test_blog_save():
    e = Entry(id=1, body="foo")
    e.save()
    e.refresh_from_db()
