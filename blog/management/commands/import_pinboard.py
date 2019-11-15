import pinboard
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import utc
from django.utils.text import slugify

from ...models import Blogmark, Tag


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        # Compare the last time we saved a bookmark locally to the latest update
        # pinboard has on the server. This isn't exactly the same since pinboard's
        # update stamp also includes edits and deletions, but I so rarely actually
        # edit/delete bookmarks that I don't really care enough to fix that
        # discrepancy at this time.

        latest_blogmark = (
            Blogmark.objects.filter(import_ref__startswith="pinboard:")
            .values("created")
            .latest("created")
        )
        latest_blogmark_timestamp = latest_blogmark["created"]
        pb = pinboard.Pinboard(settings.PINBOARD_API_KEY)
        latest_pinboard_update = pb.posts.update().replace(tzinfo=utc)
        if latest_pinboard_update <= latest_blogmark_timestamp:
            print(f"no updates since {latest_blogmark_timestamp}", file=self.stdout)
            return

        for bookmark in pb.posts.all(fromdt=latest_blogmark_timestamp, meta=1):
            if not bookmark.shared:
                print(f"{bookmark.url} is private; skipping")
                continue

            blogmark, created = Blogmark.objects.update_or_create(
                import_ref=f"pinboard:{bookmark.hash}",
                defaults={
                    "slug": slugify(bookmark.description),
                    "link_url": bookmark.url,
                    "link_title": bookmark.description,
                    "commentary": bookmark.extended,
                    "created": bookmark.time.replace(tzinfo=utc),
                    "metadata": {"pinboard_meta": bookmark.meta},
                },
            )
            blogmark.tags.set(
                Tag.objects.get_or_create(tag=tag)[0] for tag in bookmark.tags
            )
            print("created" if created else "updated", blogmark.link_url)
