from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'phone',
        'lead_score',
        'lead_quality',
        'recommended_country',
        'crm_status',
        'created_at'
    )

    list_filter = (
        'lead_quality',
        'crm_status',
        'recommended_country',
        'created_at'
    )

    search_fields = (
        'name',
        'phone',
        'email'
    )

    ordering = ('-created_at',)
