from django.db import models

import uuid
from django.contrib.auth.models import AbstractUser

class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class UserAccount(AbstractUser): # Default fields for user come from AbstractUser
    # A user of the system will have one of these roles
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin" 
        BRANCH_MANAGER = "branch_manager", "Branch Manager"
        INSTRUCTOR = "instructor", "Instructor"
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Email is the credential staff use to sign in.  `username` remains in
    # place for Django compatibility and is kept equal to this value when an
    # account is created.
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="staff",
        null=True,
        blank=True,
        help_text="Null for Super Admin, who is not scoped to a single branch.",
    )

    def __str__(self):
        return self.get_full_name() or self.username
