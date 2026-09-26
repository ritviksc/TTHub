import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey("participants.Participant", on_delete=models.PROTECT, related_name="physical_assessments")
    # Preserve the location of testing even if the participant later moves branch.
    branch = models.ForeignKey("users.Branch", on_delete=models.PROTECT)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    assessed_on = models.DateField(default=timezone.localdate)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-assessed_on", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["participant"], condition=models.Q(completed_at__isnull=True), name="one_draft_physical_assessment"),
        ]


class ExerciseResult(models.Model):
    class Exercise(models.TextChoices):
        TUG = "tug", "Timed up and go"
        CHAIR = "chair", "30-second chair stand"
        TOGETHER = "feet_together", "Feet together"
        HALF = "semi_tandem", "Half step (semi-tandem)"
        HEEL = "heel_to_toe", "Heel to toe"
        FOOT = "one_foot", "One foot"

    class Outcome(models.TextChoices):
        MEASURED = "measured", "Measured"
        UNABLE = "unable", "Unable / stopped for safety"
        ARMS = "arms_used", "Arms needed to stand"
        NOT_ATTEMPTED = "not_attempted", "Not attempted"
        SKIPPED = "skipped", "Not attempted — balance test stopped"

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="results")
    exercise = models.CharField(max_length=20, choices=Exercise.choices)
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    value = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, max_length=2000)
    walking_aid = models.CharField(max_length=150, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["assessment", "exercise"], name="one_result_per_exercise")]
