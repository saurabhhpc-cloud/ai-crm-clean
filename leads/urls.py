from django.urls import path
from . import views



urlpatterns = [
    path("", views.landing, name="landing"),
    path("chat/", views.chat_page, name="chat"),
    path("ai_chat/", views.ai_chat, name="ai_chat"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("leads/", views.lead_list, name="lead_list"),
    path("update-status/<int:lead_id>/", views.update_status, name="update_status"),
    path("export/", views.export_csv, name="export_csv"),
    path("analytics/", views.analytics, name="analytics"),
]
