import micawber
import logging
from django.db import models
from django_postgres_unlimited_varchar import UnlimitedCharField
from django.urls import reverse
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

log = logging.getLogger(__name__)


class Conference(models.Model):
    title = UnlimitedCharField()
    link = models.URLField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title


PRESENTATION_TYPE_CHOICES = [
    (i, i.title()) for i in ["keynote", "talk", "tutorial", "panel"]
]


class Presentation(models.Model):
    title = UnlimitedCharField()
    slug = models.SlugField()
    date = models.DateField()
    description = models.TextField(blank=True)

    type = UnlimitedCharField(choices=PRESENTATION_TYPE_CHOICES, default="talk")

    conference = models.ForeignKey(
        Conference, related_name="presentations", on_delete=models.CASCADE
    )

    # hm... not sure I like introducing the depedency on blog
    # so leaving this out for now.
    # but maybe I need that dep anyway -- search?
    # tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("speaking_portfolio_detail", args=[self.slug])

    @property
    def is_future(self):
        return self.date > timezone.now().date()

    @property
    def is_past(self):
        return self.date <= timezone.now().date()


COVERAGE_TYPE_CHOICES = [
    (i, i.title()) for i in ["video", "slides", "link", "notes", "write-up"]
]

FA_ICON_MAP = {
    "video": "fab fa-youtube",
    "slides": "fab fa-slideshare",
    "link": "fas fa-link",
    "notes": "fas fa-clipboard",
    "write-up": "fas fa-file-alt",
}


class Coverage(models.Model):
    presentation = models.ForeignKey(
        Presentation, related_name="coverage", on_delete=models.CASCADE
    )
    type = UnlimitedCharField(choices=COVERAGE_TYPE_CHOICES)
    url = models.URLField()
    oembed = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.presentation} - {self.type}"

    class Meta:
        verbose_name_plural = "coverage"

    def save(self, *args, **kwargs):
        providers = micawber.bootstrap_basic()
        try:
            self.oembed = providers.request(self.url)
        except micawber.ProviderException as e:
            log.warn(f"error saving oembed for {self}: {e}")
            self.oembed = {}
        super().save(*args, **kwargs)

    @property
    def icon_class(self):
        return FA_ICON_MAP[self.type]
