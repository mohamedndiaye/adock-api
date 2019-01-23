from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.postgres.fields import JSONField
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError(
                "The username must be set to create A Dock account (not France Connect)"
            )

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self._create_user(username, password, **extra_fields)


PROVIDER_A_DOCK = "AD"
PROVIDER_FRANCE_CONNECT = "FC"
PROVIDER_CHOICES = (
    (PROVIDER_A_DOCK, "A Dock"),
    (PROVIDER_FRANCE_CONNECT, "France Connect"),
)


class User(AbstractBaseUser):
    username = models.CharField(
        _("username"), max_length=255, editable=False, unique=True
    )
    email = models.EmailField(
        _("email address"), max_length=255, null=False, blank=True, default=""
    )
    first_name = models.CharField(
        _("first name"), max_length=30, null=False, blank=True, default=""
    )
    last_name = models.CharField(
        _("last name"), max_length=150, null=False, blank=True, default=""
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    provider = models.CharField(
        _("provider"), max_length=2, choices=PROVIDER_CHOICES, default="AD"
    )

    provider_data = JSONField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

    def has_perm(self, perm, obj=None):  # pylint: disable=no-self-use
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):  # pylint: disable=no-self-use
        # Simplest possible answer: Yes, always
        return True

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
