from django.db import models
from django_postgres_unlimited_varchar import UnlimitedCharField
from django.urls import reverse
from django.utils import timezone

PRESENTATION_TYPE_CHOICES = [
    (i, i.title()) for i in ["keynote", "talk", "tutorial", "panel"]
]


class Conference(models.Model):
    title = UnlimitedCharField()
    link = models.URLField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title


class Presentation(models.Model):
    title = UnlimitedCharField()
    slug = models.SlugField()
    date = models.DateField()
    description = models.TextField(blank=True)

    type = UnlimitedCharField(choices=PRESENTATION_TYPE_CHOICES, default="talk")

    conference = models.ForeignKey(
        Conference, related_name="presentations", on_delete=models.CASCADE
    )

    video_link = models.URLField(blank=True)
    slides_link = models.URLField(blank=True)
    text_link = models.URLField(blank=True)

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
