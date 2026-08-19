from django.db import models

import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ["name"]
        
    def __str__(self):
        return self.name


class UserAccount(AbstractUser):

    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        BRANCH_MANAGER = "branch_manager", "Branch Manager"
        INSTRUCTOR = "instructor", "Instructor"
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="staff",
        null=True,
        blank=True,
        help_text="Null for Super Admin, who is not scoped to a single branch.",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
 
    def __str__(self):
        return self.get_full_name() or self.username


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="participants")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to="participant_photos/", null=True, blank=True)
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
 
    class Meta:
        ordering = ["last_name", "first_name"]  # Alphabetical by surname
 
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="sessions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sessions_created"
    )
    session_date = models.DateField()
    activity = models.CharField(max_length=255)
 
    class Meta:
        ordering = ["-session_date"] 
 
    def __str__(self):
        return f"{self.activity} — {self.session_date}"


class AttendanceStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
 
    class Meta:
        verbose_name_plural = "attendance statuses"
        ordering = ["label"]
 
    def __str__(self):
        return self.label


class AbsenceReason(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
 
    class Meta:
        ordering = ["label"]
 
    def __str__(self):
        return self.label


class AttendanceRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attendance_records")
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name="attendance_records"
    )
    status = models.ForeignKey(
        AttendanceStatus, on_delete=models.PROTECT, related_name="attendance_records"
    )
    absence_reason = models.ForeignKey(
        AbsenceReason,
        on_delete=models.PROTECT,
        related_name="attendance_records",
        null=True,
        blank=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attendance_recorded"
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-recorded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "participant"], name="unique_attendance_per_session"  # Cannot record two attendance entries for the same person in the same session
            ),
        ]
 
    def __str__(self):
        return f"{self.participant} — {self.session} — {self.status}"


class PhysicalTestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="test_results")
    test_date = models.DateField()
    metrics = models.JSONField(default=dict)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="test_results_recorded"
    )
 
    class Meta:
        ordering = ["-test_date"]


class QuestionnaireResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="questionnaire_responses")
    period = models.CharField(max_length=20, help_text='e.g. "2026-Q3"')
    answers = models.JSONField(default=dict)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="questionnaires_submitted"
    )
 
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "period"], name="unique_questionnaire_per_branch_period"
            ),
        ]


class Feedback(models.Model):
    class FeedbackType(models.TextChoices):
        QUOTE = "quote", "Quote / story"
        OBSERVATION = "observation", "Observation"
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="feedback")
    participant = models.ForeignKey(
        Participant, on_delete=models.SET_NULL, related_name="feedback", null=True, blank=True
    )
    session = models.ForeignKey(
        Session, on_delete=models.SET_NULL, related_name="feedback", null=True, blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="feedback_authored"
    )
    type = models.CharField(max_length=20, choices=FeedbackType.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(participant__isnull=False) | models.Q(session__isnull=False),
                name="feedback_has_participant_or_session",
            ),
        ]


class SummaryReport(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="summary_reports",
        null=True,
        blank=True,
        help_text="Null for a national (all-branch) report.",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    narrative = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="summaries_approved",
        null=True,
        blank=True,
    )
 
    class Meta:
        ordering = ["-period_start"]
        

class SummaryCitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    summary = models.ForeignKey(SummaryReport, on_delete=models.CASCADE, related_name="citations")
    feedback = models.ForeignKey(Feedback, on_delete=models.PROTECT, related_name="citations")
    excerpt = models.TextField(help_text="Exact substring of feedback.content used as evidence.")
 

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_entries"
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    timestamp = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-timestamp"]