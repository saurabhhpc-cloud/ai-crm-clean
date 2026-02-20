import os
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.http import HttpResponse

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework import status

from openai import OpenAI
from .models import Lead


# =====================================
# LANDING PAGE
# =====================================

def landing(request):
    return render(request, "leads/landing.html")


def chat_page(request):
    return render(request, "leads/chat.html")


# =====================================
# DASHBOARD
# =====================================

@login_required
def dashboard(request):
    total = Lead.objects.count()
    hot = Lead.objects.filter(lead_quality__icontains="Hot").count()
    warm = Lead.objects.filter(lead_quality__icontains="Warm").count()
    cold = Lead.objects.filter(lead_quality__icontains="Cold").count()
    converted = Lead.objects.filter(crm_status="converted").count()

    return render(request, "leads/dashboard.html", {
        "total": total,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "converted": converted,
    })


# =====================================
# ANALYTICS
# =====================================

@login_required
def analytics(request):

    monthly_leads = (
        Lead.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    monthly_converted = (
        Lead.objects
        .filter(crm_status="converted")
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    labels = []
    lead_data = []
    converted_data = []

    converted_dict = {item['month']: item['total'] for item in monthly_converted}

    for item in monthly_leads:
        month = item['month'].strftime("%b %Y")
        labels.append(month)
        lead_data.append(item['total'])
        converted_data.append(converted_dict.get(item['month'], 0))

    hot = Lead.objects.filter(lead_quality__icontains="Hot").count()
    warm = Lead.objects.filter(lead_quality__icontains="Warm").count()
    cold = Lead.objects.filter(lead_quality__icontains="Cold").count()

    context = {
        "labels": labels,
        "lead_data": lead_data,
        "converted_data": converted_data,
        "hot": hot,
        "warm": warm,
        "cold": cold
    }

    return render(request, "leads/analytics.html", context)


# =====================================
# LEAD LIST
# =====================================

@login_required
def lead_list(request):

    query = request.GET.get("q")
    status_filter = request.GET.get("status")

    leads = Lead.objects.all().order_by("-created_at")

    if query:
        leads = leads.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    if status_filter:
        leads = leads.filter(crm_status=status_filter)

    paginator = Paginator(leads, 10)
    page_number = request.GET.get("page")
    leads = paginator.get_page(page_number)

    return render(request, "leads/lead_list.html", {
        "leads": leads
    })


# =====================================
# UPDATE STATUS
# =====================================

@login_required
def update_status(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == "POST":
        lead.crm_status = request.POST.get("status")
        lead.assigned_to_id = request.POST.get("assigned_to")
        lead.save()

    return redirect("lead_list")


# =====================================
# EXPORT CSV
# =====================================

@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Phone", "Score", "Quality", "Country", "Status"])

    leads = Lead.objects.all()

    for lead in leads:
        writer.writerow([
            lead.name,
            lead.phone,
            lead.lead_score,
            lead.lead_quality,
            lead.recommended_country,
            lead.crm_status
        ])

    return response


# =====================================
# AI CHAT API (OPENAI INTEGRATED)
# =====================================

@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def ai_chat(request):

    try:
        data = request.data

        user_summary = data.get("user_summary", "").strip()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        country_interest = data.get("country_interest", "")
        course_interest = data.get("course_interest", "")
        intake = data.get("intake", "September")
        qualification = data.get("qualification", "12th")
        backlogs = data.get("backlogs", False)

        try:
            ielts_score = float(data.get("ielts_score")) if data.get("ielts_score") else None
        except:
            ielts_score = None

        try:
            budget = int(data.get("budget")) if data.get("budget") else None
        except:
            budget = None

        if not user_summary or not name or not phone:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create Lead (score auto calculated)
        lead = Lead.objects.create(
            name=name,
            email=email,
            phone=phone,
            country_interest=country_interest,
            course_interest=course_interest,
            ielts_score=ielts_score,
            budget=budget,
            intake=intake,
            qualification=qualification,
            backlogs=backlogs
        )

        score = lead.lead_score
        recommended_country = lead.recommended_country
        lead_quality = lead.lead_quality

        # ===============================
        # OPENAI CALL
        # ===============================

        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional Study Abroad Assistant. Use only provided data. Do not assume extra details. Format response clearly."
                    },
                    {
                        "role": "user",
                        "content": f"""
AI PROFILE ANALYSIS:
Score: {score}
Recommended Country: {recommended_country}
Lead Category: {lead_quality}

USER_SUMMARY:
{user_summary}
"""
                    }
                ],
                temperature=0.3,
            )

            ai_text = completion.choices[0].message.content

        except Exception as e:
            print("OpenAI Error:", e)
            ai_text = f"""
📋 Student Profile Summary

Name: {name}
IELTS: {ielts_score}
Budget: {budget} Lakhs

🤖 AI Profile Analysis
• Eligibility Score: {score}%
• Recommended Country: {recommended_country}
• Lead Category: {lead_quality}

📌 Next Step:
Our counsellor will contact you shortly.
"""

        return Response({
            "success": True,
            "ai_reply": ai_text,
            "score": score,
            "recommended_country": recommended_country,
            "lead_quality": lead_quality
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)})
