from django.shortcuts import render, get_object_or_404
from .models import Presentation
from django.utils import timezone


def index(request):
    talks = Presentation.objects.order_by("-date")
    return render(
        request,
        "speaking_portfolio/index.html",
        {
            "future_presentations": talks.filter(date__gt=timezone.now().date()),
            "past_presentations": talks.filter(date__lte=timezone.now().date()),
        },
    )


def detail(request, slug):
    return render(
        request,
        "speaking_portfolio/detail.html",
        {"presentation": get_object_or_404(Presentation, slug=slug)},
    )
