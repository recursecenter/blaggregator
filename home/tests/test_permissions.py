from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
import requests

from home.models import Blog, Hacker, User
from home.permissions import BLOCK_CRAWLING, has_current_staff_stint, is_recurse_staff

FAST_HASHER = ["django.contrib.auth.hashers.MD5PasswordHasher"]
BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "home.permissions.StaffBackend",
)
STAFF_PROFILE = {"stints": [{"type": "employment", "end_date": None}]}
FORMER_STAFF_PROFILE = {"stints": [{"type": "employment", "end_date": "2020-01-31"}]}
BATCH_PROFILE = {"stints": [{"type": "retreat", "end_date": None}]}


def fake_api_response(profile=None, error=None):
    def get(url, **kwargs):
        if error is not None:
            raise error
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: profile
        return response

    return get


class HasCurrentStaffStintTestCase(TestCase):
    def test_ongoing_employment_is_staff(self):
        self.assertTrue(has_current_staff_stint(STAFF_PROFILE))

    def test_ended_employment_is_not_staff(self):
        self.assertFalse(has_current_staff_stint(FORMER_STAFF_PROFILE))

    def test_other_stints_are_not_staff(self):
        self.assertFalse(has_current_staff_stint(BATCH_PROFILE))

    def test_missing_or_null_stints_are_not_staff(self):
        self.assertFalse(has_current_staff_stint({}))
        self.assertFalse(has_current_staff_stint({"stints": None}))


@override_settings(AUTHENTICATION_BACKENDS=BACKENDS, PASSWORD_HASHERS=FAST_HASHER)
class StaffPermissionTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("someone", password="test")

    def tearDown(self):
        cache.clear()

    def check(self, profile=None, error=None, user=None):
        user = user or self.user
        api = fake_api_response(profile, error)
        with patch("home.permissions.requests.get", side_effect=api) as get:
            return User.objects.get(pk=user.pk).has_perm(BLOCK_CRAWLING), get

    def test_staff_has_permission(self):
        allowed, _ = self.check(STAFF_PROFILE)
        self.assertTrue(allowed)

    def test_non_staff_does_not_have_permission(self):
        allowed, _ = self.check(FORMER_STAFF_PROFILE)
        self.assertFalse(allowed)

    def test_other_permissions_are_not_granted(self):
        with patch("home.permissions.requests.get") as get:
            self.assertFalse(self.user.has_perm("home.delete_blog"))
        get.assert_not_called()

    def test_inactive_user_does_not_have_permission(self):
        self.user.is_active = False
        self.user.save()
        with patch("home.permissions.requests.get") as get:
            self.assertFalse(self.user.has_perm(BLOCK_CRAWLING))
        get.assert_not_called()

    def test_superuser_has_permission_without_calling_the_api(self):
        self.user.is_superuser = True
        self.user.save()
        with patch("home.permissions.requests.get") as get:
            self.assertTrue(self.user.has_perm(BLOCK_CRAWLING))
        get.assert_not_called()

    def test_result_is_cached(self):
        api = fake_api_response(STAFF_PROFILE)
        with patch("home.permissions.requests.get", side_effect=api) as get:
            self.assertTrue(is_recurse_staff(self.user))
            self.assertTrue(is_recurse_staff(self.user))
        self.assertEqual(1, get.call_count)

    def test_negative_result_is_cached(self):
        api = fake_api_response(BATCH_PROFILE)
        with patch("home.permissions.requests.get", side_effect=api) as get:
            self.assertFalse(is_recurse_staff(self.user))
            self.assertFalse(is_recurse_staff(self.user))
        self.assertEqual(1, get.call_count)

    def test_api_errors_deny_access(self):
        error = requests.ConnectionError("https://www.recurse.com/?access_token=secret")
        allowed, _ = self.check(error=error)
        self.assertFalse(allowed)

    def test_api_errors_are_cached_briefly_and_then_retried(self):
        error = requests.Timeout()
        with patch("home.permissions.requests.get", side_effect=fake_api_response(error=error)) as get:
            self.assertFalse(is_recurse_staff(self.user))
            self.assertFalse(is_recurse_staff(self.user))
        self.assertEqual(1, get.call_count)
        # Once the failure expires, the next check asks the API again
        cache.clear()
        allowed, _ = self.check(STAFF_PROFILE)
        self.assertTrue(allowed)

    def test_http_errors_deny_access(self):
        def get(url, **kwargs):
            response = requests.Response()
            response.status_code = 404
            return response

        with patch("home.permissions.requests.get", side_effect=get):
            self.assertFalse(is_recurse_staff(self.user))

    def test_invalid_json_denies_access(self):
        allowed, _ = self.check(error=ValueError("no json"))
        self.assertFalse(allowed)


@override_settings(AUTHENTICATION_BACKENDS=BACKENDS, PASSWORD_HASHERS=FAST_HASHER)
class BlockCrawlingViewTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user("owner", password="test")
        Hacker.objects.create(user=self.owner)
        self.blog = Blog.objects.create(user=self.owner, feed_url="http://example.com/feed")
        self.moderator = User.objects.create_user("moderator", password="test")
        self.url = "/block_crawling/{}/".format(self.blog.id)

    def tearDown(self):
        cache.clear()
        User.objects.all().delete()

    def post_as(self, user, profile=None, error=None):
        if user is not None:
            self.client.login(username=user.username, password="test")
        api = fake_api_response(profile, error)
        with patch("home.permissions.requests.get", side_effect=api):
            return self.client.post(self.url)

    def is_skipped(self):
        return Blog.objects.get(pk=self.blog.pk).skip_crawl

    def test_anonymous_user_is_sent_to_login(self):
        response = self.post_as(None)
        self.assertRedirects(response, "/login/?next={}".format(self.url))
        self.assertFalse(self.is_skipped())

    def test_non_staff_gets_forbidden(self):
        response = self.post_as(self.moderator, BATCH_PROFILE)
        self.assertEqual(403, response.status_code)
        self.assertFalse(self.is_skipped())

    def test_owner_who_is_not_staff_cannot_block(self):
        response = self.post_as(self.owner, BATCH_PROFILE)
        self.assertEqual(403, response.status_code)
        self.assertFalse(self.is_skipped())

    def test_api_failure_gets_forbidden(self):
        response = self.post_as(self.moderator, error=requests.Timeout())
        self.assertEqual(403, response.status_code)
        self.assertFalse(self.is_skipped())

    def test_staff_can_block_crawling(self):
        response = self.post_as(self.moderator, STAFF_PROFILE)
        self.assertRedirects(
            response, "/profile/{}/".format(self.owner.id), fetch_redirect_response=False
        )
        self.assertTrue(self.is_skipped())

    def test_superuser_can_block_crawling(self):
        self.moderator.is_superuser = True
        self.moderator.save()
        response = self.post_as(self.moderator, error=requests.Timeout())
        self.assertEqual(302, response.status_code)
        self.assertTrue(self.is_skipped())

    def test_get_is_not_allowed(self):
        self.client.login(username="moderator", password="test")
        self.moderator.is_superuser = True
        self.moderator.save()
        self.assertEqual(405, self.client.get(self.url).status_code)
        self.assertFalse(self.is_skipped())

    def test_unknown_blog_is_404(self):
        self.moderator.is_superuser = True
        self.moderator.save()
        self.client.login(username="moderator", password="test")
        self.assertEqual(404, self.client.post("/block_crawling/99999/").status_code)

    def test_button_is_shown_only_to_staff(self):
        profile_url = "/profile/{}/".format(self.owner.id)
        self.client.login(username="moderator", password="test")
        with patch("home.permissions.requests.get", side_effect=fake_api_response(BATCH_PROFILE)):
            self.assertNotContains(self.client.get(profile_url), self.url)
        cache.clear()
        with patch("home.permissions.requests.get", side_effect=fake_api_response(STAFF_PROFILE)):
            self.assertContains(self.client.get(profile_url), self.url)
