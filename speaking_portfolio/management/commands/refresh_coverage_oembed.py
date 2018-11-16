from django.core.management.base import BaseCommand
from ...models import Coverage


class Command(BaseCommand):
    help = "Re-fetch oembed data for all coverage"

    def handle(self, *args, **kwargs):
        for c in Coverage.objects.all():
            c.save()
