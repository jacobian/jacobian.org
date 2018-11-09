from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="speaking_portfolio_index"),
    path("<slug:slug>/", views.detail, name="speaking_portfolio_detail"),
]
