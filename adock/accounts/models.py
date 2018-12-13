from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    PROVIDER_CHOICES = (("AD", "A Dock"), ("FC", "France Connect"))

    username = models.CharField(_("username"), max_length=255, editable=False)
    email = models.EmailField(
        verbose_name=_("email address"),
        max_length=255,
        unique=True,
    )
    provider = models.CharField(
        _("provider"), max_length=2, choices=PROVIDER_CHOICES, default="AD"
    )
    provider_data = JSONField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        # We'll see later if it could be different.
        # For now, it's convenient to submit username or email as login field
        self.username = self.email
        super().save(*args, **kwargs)
