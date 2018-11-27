import json
from django.shortcuts import render
import pathlib


def resume(request):
    with (pathlib.Path(__file__).parent / "resume.json").open() as fp:
        resume_data = json.load(fp)
    return render(request, "resume.html", {"resume": resume_data})
