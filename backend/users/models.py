from django.db import models

import uuid
from django.contrib.auth.models import AbstractUser

class UserAccount(AbstractUser): # Default fields for user come from AbstractUser

    # A user of the system will have one of these roles
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin" 
        BRANCH_MANAGER = "branch_manager", "Branch Manager"
        INSTRUCTOR = "instructor", "Instructor"
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices)
 
    def __str__(self):
        return self.get_full_name() or self.username
