from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return render(request, "leads/landing.html")


urlpatterns = [
    path('', home),
    path("admin/", admin.site.urls),
    path("chat/", TemplateView.as_view(template_name="leads/chatbot.html")),
    path("", include("leads.urls")),
    path("api/", include("api.urls")),
]