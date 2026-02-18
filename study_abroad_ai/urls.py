from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chat/", TemplateView.as_view(template_name="leads/chatbot.html")),
    path("", include("leads.urls")),
]