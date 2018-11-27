import re
from collections import Counter
from xml.etree import ElementTree

import arrow
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe
from django_postgres_unlimited_varchar import UnlimitedCharField
from django.utils.text import Truncator

tag_re = re.compile("^[a-z0-9]+$")


class Tag(models.Model):
    tag = models.SlugField(unique=True)

    def __str__(self):
        return self.tag

    def get_absolute_url(self):
        return reverse("tag_detail", args=[self.tag])

    def get_link(self, reltag=False):
        return mark_safe(
            '<a href="%s"%s>%s</a>'
            % (self.get_absolute_url(), (reltag and ' rel="tag"' or ""), self)
        )

    def get_reltag(self):
        return self.get_link(reltag=True)

    def entry_count(self):
        return self.entry_set.count()

    def link_count(self):
        return self.blogmark_set.count()

    def quote_count(self):
        return self.quotation_set.count()

    def total_count(self):
        return self.entry_count() + self.link_count() + self.quote_count()

    def all_types_queryset(self):
        entries = (
            self.entry_set.all()
            .annotate(type=models.Value("entry", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        blogmarks = (
            self.blogmark_set.all()
            .annotate(type=models.Value("blogmark", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        quotations = (
            self.quotation_set.all()
            .annotate(type=models.Value("quotation", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        return entries.union(blogmarks, quotations).order_by("-created")

    def get_related_tags(self, limit=10):
        """Get all items tagged with this, look at /their/ tags, order by count"""
        if not hasattr(self, "_related_tags"):
            counts = Counter()
            for klass, collection in (
                (Entry, "entry_set"),
                (Blogmark, "blogmark_set"),
                (Quotation, "quotation_set"),
            ):
                qs = klass.objects.filter(
                    pk__in=getattr(self, collection).all()
                ).values_list("tags__tag", flat=True)
                counts.update(t for t in qs if t != self.tag)
            self._related_tags = [p[0] for p in counts.most_common(limit)]
        return self._related_tags


class BaseModel(models.Model):
    created = models.DateTimeField(default=timezone.now)
    tags = models.ManyToManyField(Tag, blank=True)
    slug = models.SlugField(max_length=64)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    metadata = JSONField(blank=True, default=dict)
    search_document = SearchVectorField(null=True)
    import_ref = models.TextField(max_length=64, null=True, unique=True)

    @property
    def type(self):
        return self._meta.model_name

    def created_unixtimestamp(self):
        return arrow.get(self.created).timestamp

    def tag_summary(self):
        return " ".join(t.tag for t in self.tags.all())

    def get_absolute_url(self):
        d = timezone.localdate(self.created)
        return reverse("blog_archive_item", args=[d.year, d.month, d.day, self.slug])

    def edit_url(self):
        return "/admin/blog/%s/%d/" % (self.__class__.__name__.lower(), self.id)

    class Meta:
        abstract = True
        ordering = ("-created",)
        indexes = [GinIndex(fields=["search_document"])]


class Series(models.Model):
    title = UnlimitedCharField()
    slug = models.SlugField()
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("series-detail", args=[self.slug])

    def get_entries_in_order(self):
        return self.entries.order_by("created")


class Entry(BaseModel):
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    tweet_html = models.TextField(
        blank=True,
        null=True,
        help_text="""
        Paste in the embed tweet HTML, minus the script tag,
        to display a tweet in the sidebar next to this entry.
    """.strip(),
    )
    extra_head_html = models.TextField(
        blank=True,
        null=True,
        help_text="""
        Extra HTML to be included in the &lt;head&gt; for this entry
    """.strip(),
    )
    series = models.ForeignKey(
        Series, related_name="entries", blank=True, null=True, on_delete=models.SET_NULL
    )

    is_entry = True

    def images(self):
        """Extracts images from entry.body"""
        et = ElementTree.fromstring("<entry>%s</entry>" % self.body)
        return [i.attrib for i in et.findall(".//img")]

    def index_components(self):
        return {
            "A": self.title,
            "C": strip_tags(self.body),
            "B": " ".join(self.tags.values_list("tag", flat=True)),
        }

    def __str__(self):
        return (
            self.title
            if self.title
            else Truncator(strip_tags(self.body)).words(15, truncate=" …")
        )

    class Meta(BaseModel.Meta):
        verbose_name_plural = "Entries"


class Quotation(BaseModel):
    quotation = models.TextField()
    source = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True)

    is_quotation = True

    def title(self):
        """Mainly a convenence for the comments RSS feed"""
        return "A quote from %s" % escape(self.source)

    def index_components(self):
        return {
            "A": self.quotation,
            "B": " ".join(self.tags.values_list("tag", flat=True)),
            "C": self.source,
        }

    def __str__(self):
        return self.quotation


class Blogmark(BaseModel):
    link_url = models.URLField(max_length=1000)
    link_title = models.CharField(max_length=255)
    via_url = models.URLField(blank=True, null=True)
    via_title = models.CharField(max_length=255, blank=True, null=True)
    commentary = models.TextField()

    is_blogmark = True

    def index_components(self):
        return {
            "A": self.link_title,
            "B": " ".join(self.tags.values_list("tag", flat=True)),
            "C": " ".join(
                [self.commentary, self.link_domain(), (self.via_title or "")]
            ),
        }

    def __str__(self):
        return self.link_title

    def link_domain(self):
        return self.link_url.split("/")[2]

    def word_count(self):
        count = len(self.commentary.split())
        if count == 1:
            return "1 word"
        else:
            return "%d words" % count


class Photo(BaseModel):
    photo = models.ImageField(upload_to="photos/%Y")
    title = UnlimitedCharField(blank=True)

    def __str__(self):
        return self.title if self.title else self.photo.url

    def index_components(self):
        return {
            "A": self.title,
            "B": " ".join(self.tags.values_list("tag", flat=True)),
            "C": "",
        }


def load_mixed_objects(dicts):
    """
    Takes a list of dictionaries, each of which must at least have a 'type'
    and a 'pk' key. Returns a list of ORM objects of those various types.

    Each returned ORM object has a .original_dict attribute populated.
    """
    to_fetch = {}
    for d in dicts:
        to_fetch.setdefault(d["type"], set()).add(d["pk"])
    fetched = {}
    for key, model in (
        ("blogmark", Blogmark),
        ("entry", Entry),
        ("quotation", Quotation),
    ):
        ids = to_fetch.get(key) or []
        objects = model.objects.prefetch_related("tags").filter(pk__in=ids)
        for obj in objects:
            fetched[(key, obj.pk)] = obj
    # Build list in same order as dicts argument
    to_return = []
    for d in dicts:
        item = fetched.get((d["type"], d["pk"])) or None
        if item:
            item.original_dict = d
        to_return.append(item)
    return to_return
