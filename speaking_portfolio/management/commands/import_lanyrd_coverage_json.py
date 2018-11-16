import requests
import json
from django.utils.text import slugify
from django.core.management.base import BaseCommand
from ...models import Presentation, Coverage, Conference


class Command(BaseCommand):
    help = "load coverage data scraped from lanyrd into json"

    def add_arguments(self, parser):
        parser.add_argument(
            "url_or_path_to_json", type=str, help="URL or path to JSON to import"
        )

    def handle(self, url_or_path_to_json, *args, **kwargs):

        is_url = url_or_path_to_json.startswith(
            "http://"
        ) or url_or_path_to_json.startswith("https://")

        if is_url:
            data = requests.get(url_or_path_to_json).json()
        else:
            data = json.load(open(url_or_path_to_json))

        for coverage_url, coverage_detail in data.items():
            # Skip existing coverage
            if Coverage.objects.filter(url=coverage_url).exists():
                continue

            # Skip coverage that was scraped with an error
            if "error" in coverage_detail["conference"]:
                continue

            # Look for an existing presentation
            talk_slug = slugify(coverage_detail["talk_title"])[:50]
            try:
                presentation = Presentation.objects.get(
                    slug=talk_slug,
                    conference__title=coverage_detail["conference"]["title"],
                )
            except Presentation.DoesNotExist:
                conference, created = Conference.objects.update_or_create(
                    title=coverage_detail["conference"]["title"],
                    defaults={
                        "link": coverage_detail["conference"]["link"],
                        "start_date": coverage_detail["start_date"],
                        "end_date": coverage_detail["end_date"],
                    },
                )
                if created:
                    print(f"Created {conference.title}")

                presentation = Presentation.objects.create(
                    conference=conference,
                    title=coverage_detail["talk_title"],
                    slug=talk_slug,
                    date=coverage_detail["start_date"],
                )
                print(f"Created {presentation.title}")

            coverage = presentation.coverage.create(
                type=coverage_detail["type"], url=coverage_url
            )
            print(f"Created {coverage}")
