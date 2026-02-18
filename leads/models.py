from django.db import models
from django.contrib.auth.models import User


class Lead(models.Model):

    QUALIFICATION_CHOICES = [
        ('12th', '12th'),
        ('Graduation', 'Graduation'),
    ]

    CRM_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('followup', 'Follow-up'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]

    # Basic Info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    country_interest = models.CharField(max_length=50, blank=True)
    course_interest = models.CharField(max_length=100, blank=True)

    ielts_score = models.FloatField(null=True, blank=True)
    budget = models.IntegerField(null=True, blank=True)

    qualification = models.CharField(
        max_length=20,
        choices=QUALIFICATION_CHOICES,
        default='12th'
    )

    backlogs = models.BooleanField(default=False)
    intake = models.CharField(max_length=20)
    assigned_to = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)


    # Intelligent Fields
    lead_score = models.IntegerField(default=0)
    recommended_country = models.CharField(max_length=50, blank=True)
    lead_quality = models.CharField(max_length=20, blank=True)

    # CRM Field
    crm_status = models.CharField(
        max_length=20,
        choices=CRM_STATUS_CHOICES,
        default='new'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------
    # SCORE CALCULATION
    # ---------------------------
    def calculate_score(self):
        score = 0

        # IELTS
        if self.ielts_score:
            if self.ielts_score >= 7:
                score += 30
            elif self.ielts_score >= 6:
                score += 20
            elif self.ielts_score >= 5.5:
                score += 10
            else:
                score += 5

        # Budget
        if self.budget:
            if self.budget >= 30:
                score += 30
            elif self.budget >= 25:
                score += 25
            elif self.budget >= 20:
                score += 15
            elif self.budget >= 15:
                score += 10
            else:
                score += 5

        # Qualification
        score += 20 if self.qualification == "Graduation" else 10

        # Backlogs
        score += 20 if not self.backlogs else -10

        return score

    # ---------------------------
    # COUNTRY RECOMMENDATION
    # ---------------------------
    def get_country_recommendation(self):

        if not self.budget:
            return "Singapore 🇸🇬"

        if self.budget >= 30:
            return "Australia 🇦🇺"
        elif self.budget >= 25:
            return "UK 🇬🇧"
        elif self.budget >= 15:
            return "Dubai 🇦🇪"
        else:
            return "Singapore 🇸🇬"

    # ---------------------------
    # LEAD QUALITY (Hot/Warm/Cold)
    # ---------------------------
    def get_lead_quality(self):
        if self.lead_score >= 85:
            return "Hot 🔥"
        elif self.lead_score >= 65:
            return "Warm 🟡"
        else:
            return "Cold 🔵"

    # ---------------------------
    # AUTO SAVE
    # ---------------------------
    def save(self, *args, **kwargs):
        self.lead_score = self.calculate_score()
        self.recommended_country = self.get_country_recommendation()
        self.lead_quality = self.get_lead_quality()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} | {self.lead_quality}"
