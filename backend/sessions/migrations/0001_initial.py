# Generated manually for the initial sessions app schema.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("participants", "0002_participant_gp_consent_date_and_more"),
        ("users", "0003_useraccount_email_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProgrammeSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("time", models.TimeField()),
                ("activity", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="programme_sessions", to="users.branch")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_sessions", to="users.useraccount")),
            ],
            options={"ordering": ["-date", "-time"]},
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("present", "Present"), ("absent", "Absent")], default="absent", max_length=10)),
                ("absence_reason", models.CharField(blank=True, choices=[("no_show", "No show"), ("medical_appointment", "Medical appointment"), ("transport_issue", "Transport issue"), ("other", "Other")], max_length=30)),
                ("absence_reason_other", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attendance_records", to="participants.participant")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance", to="programme_sessions.programmesession")),
            ],
            options={"ordering": ["participant__last_name", "participant__first_name"]},
        ),
        migrations.AddConstraint(
            model_name="attendancerecord",
            constraint=models.UniqueConstraint(fields=("session", "participant"), name="one_attendance_record_per_participant"),
        ),
    ]
