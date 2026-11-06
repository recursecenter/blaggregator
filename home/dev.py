"""Helpers for local development.  See docs/development.md."""

from home.models import Hacker, User

DEV_USERNAME = "dev@example.com"


def get_dev_user():
    """Get (or create) a superuser for local development."""
    user, created = User.objects.get_or_create(
        username=DEV_USERNAME,
        defaults={
            "first_name": "Dev",
            "last_name": "User",
            "email": DEV_USERNAME,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    Hacker.objects.get_or_create(user=user)
    return user
