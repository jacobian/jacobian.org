import pytest
from blog.factories import EntryFactory, BlogmarkFactory, QuotationFactory


def assert_template_used(response, template):
    assert template in [t.name for t in response.templates]


@pytest.mark.django_db
def test_homepage(client):
    db_entries = [EntryFactory(), EntryFactory(), EntryFactory()]
    BlogmarkFactory()
    QuotationFactory()
    response = client.get("/")
    entries = response.context["entries"]

    expected = [e.pk for e in sorted(db_entries, key=lambda e: e.created, reverse=True)]
    actual = [e.pk for e in entries]

    assert expected == actual


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,factory",
    [
        ("entry", EntryFactory),
        ("blogmark", BlogmarkFactory),
        ("quotation", QuotationFactory),
    ],
)
def test_entry_detail(name, factory, client):
    obj = factory()
    response = client.get(obj.get_absolute_url())
    assert_template_used(response, f"{name}.html")
    assert name in response.context
    assert response.context[name] == obj
