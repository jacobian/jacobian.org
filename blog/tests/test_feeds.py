import pytest
from blog.factories import EntryFactory, BlogmarkFactory, QuotationFactory
from blog.feeds import sitemap
from lxml import etree


@pytest.mark.django_db
def test_sitemap_xml(rf):
    request = rf.get("/sitemap.xml")
    objects = [EntryFactory(), BlogmarkFactory(), QuotationFactory()]
    expected_urls = {request.build_absolute_uri(o.get_absolute_url()) for o in objects}

    response = sitemap(request)
    doc = etree.fromstring(response.content)
    actual_urls = {
        e.text
        for e in doc.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    }
    assert expected_urls == actual_urls
