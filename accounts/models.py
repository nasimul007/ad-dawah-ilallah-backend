from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from accounts.manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    # Core login field
    username = models.CharField(max_length=100, unique=True)

    # Optional contact fields
    phone = models.CharField(max_length=25, null=True, blank=True)
    email = models.EmailField(max_length=150, null=True, blank=True)

    # Basic profile data
    full_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.CharField(max_length=255, null=True, blank=True)

    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=150, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=25, null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    # Django-required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # allows admin panel access

    roles = models.ManyToManyField(
        "Role",
        blank=True,
        related_name="users",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"    # login with username
    REQUIRED_FIELDS = []           # for createsuperuser

    def __str__(self):
        return f"{self.full_name} ({self.username})"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many permissions under one role
    permissions = models.ManyToManyField(
        "Permission",
        blank=True,
        related_name="roles",
    )

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)   # e.g. COURSE_CREATE
    module = models.CharField(max_length=50)               # e.g. courses, finance
    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.module}: {self.code}"