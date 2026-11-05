"""Privileges for Recurse Center staff.

Whether someone is staff is not stored in our DB.  It is looked up from their
stints on the Recurse Center API, and the answer is cached for a while.  The
``StaffBackend`` plugs this into Django's permission system, so that
``@permission_required(BLOCK_CRAWLING)`` and ``{% if perms.home.block_crawling %}``
both work.  Superusers always pass these checks (Django handles that itself).

"""

import logging

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.core.cache import cache
import requests

from home.oauth import HackerSchoolOAuth2

log = logging.getLogger("blaggregator")

# Permission names that Recurse staff are granted.  These don't exist in the DB.
BLOCK_CRAWLING = "home.block_crawling"
STAFF_PERMISSIONS = {BLOCK_CRAWLING}

# A current stint of this type means that the person works at Recurse.
STAFF_STINT_TYPE = "employment"
# How long we trust a lookup, in seconds.  This bounds how stale access can be.
STAFF_CACHE_SECONDS = 60 * 60
# How long to remember that a lookup failed, so a slow or broken API doesn't
# make every check (the profile page does one per blog) wait for the timeout.
FAILURE_CACHE_SECONDS = 60
API_TIMEOUT_SECONDS = 5


def has_current_staff_stint(profile):
    """Return True if the RC API profile has an ongoing staff stint."""
    return any(
        stint.get("type") == STAFF_STINT_TYPE and stint.get("end_date") is None
        for stint in profile.get("stints") or []
    )


def fetch_is_recurse_staff(user_id):
    """Ask the RC API if the user is staff.  Returns None if it can't tell."""
    url = "{}/api/v1/profiles/{}".format(HackerSchoolOAuth2.HACKER_SCHOOL_ROOT, user_id)
    try:
        response = requests.get(
            url,
            params={"access_token": settings.HS_PERSONAL_TOKEN},
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        profile = response.json()
    except (requests.RequestException, ValueError) as e:
        # Log only the exception type: the message includes the URL, and
        # therefore the access token.
        log.error(
            "Could not check Recurse stints for user %s: %s", user_id, type(e).__name__
        )
        return None
    return has_current_staff_stint(profile)


def is_recurse_staff(user):
    """Cached check if the user is currently staff at Recurse.  Fails closed."""
    key = "recurse-staff:{}".format(user.pk)
    is_staff = cache.get(key)
    if is_staff is None:
        is_staff = fetch_is_recurse_staff(user.pk)
        if is_staff is None:
            # Fail closed, and look again soon.
            cache.set(key, False, FAILURE_CACHE_SECONDS)
            return False
        cache.set(key, is_staff, STAFF_CACHE_SECONDS)
    return is_staff


class StaffBackend(BaseBackend):
    """Grants ``STAFF_PERMISSIONS`` to people with a current staff stint."""

    def has_perm(self, user_obj, perm, obj=None):
        if perm not in STAFF_PERMISSIONS or not user_obj.is_active:
            return False
        return is_recurse_staff(user_obj)
