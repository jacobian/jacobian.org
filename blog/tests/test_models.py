from blog.models import Entry


def test_entry_no_title():
    e = Entry(body="xyzfoo")
    assert str(e) == "xyzfoo"
