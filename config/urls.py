from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from blog.views import blog as blog_views
from blog.views import micropub as micropub_views
from blog import feeds
from feedstats.utils import count_subscribers
from . import url_converters

url_converters.register_all()

urlpatterns = [
    path("", blog_views.index),
    path("<year:year>/", blog_views.archive_year, name="blog_archive_year"),
    path(
        "<year:year>/<month:month>/",
        blog_views.archive_month,
        name="blog_archive_month",
    ),
    path(
        "<year:year>/<month:month>/<day:day>/",
        blog_views.archive_day,
        name="blog_archive_day",
    ),
    path(
        "<year:year>/<month:month>/<day:day>/<slug:slug>/",
        blog_views.archive_item,
        name="blog_archive_item",
    ),
    path("search/", blog_views.search, name="search"),
    path("tags/", blog_views.tag_index, name="tag_index"),
    path("tags/<tags>/", blog_views.archive_tag, name="tag_detail"),
    path(
        "atom/entries/", count_subscribers(feeds.Entries().__call__), name="blog_feed"
    ),
    path("atom/links/", count_subscribers(feeds.Blogmarks().__call__)),
    path("atom/everything/", count_subscribers(feeds.Everything().__call__)),
    path("sitemap.xml", feeds.sitemap),
    path("tools/", blog_views.tools),
    path("tools/extract-title/", blog_views.tools_extract_title),
    path("tools/search-tags/", blog_views.tools_search_tags),
    path("write/", blog_views.write),
    path("admin/", admin.site.urls),
    path("speaking/", include("speaking_portfolio.urls")),
    path("writing/", blog_views.entry_archive, name="entry_archive"),
    path("writing/<slug:slug>/", blog_views.redirect_old_blog_urls),
    path("feed.xml", blog_views.redirect_old_feed),
    path("feed/", blog_views.redirect_old_feed),
    path("rss/summary/", blog_views.redirect_old_feed),
    path("rss/full/", blog_views.redirect_old_feed),
    path("micropub", micropub_views.Micropub.as_view(), name="micropub"),
    path(
        "micropub/media", micropub_views.MicropubMedia.as_view(), name="micropub_media"
    ),
]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
