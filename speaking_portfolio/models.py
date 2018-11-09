from django.db import models
from django_postgres_unlimited_varchar import UnlimitedCharField
from django.urls import reverse


class Presentation(models.Model):
    title = UnlimitedCharField()
    slug = models.SlugField()
    date = models.DateField()
    description = models.TextField(blank=True)

    conference_title = UnlimitedCharField()
    conference_link = models.URLField(blank=True)

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
