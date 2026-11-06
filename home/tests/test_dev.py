from django.test import TestCase, override_settings
from django.urls import reverse

from home.dev import DEV_USERNAME
from home.models import Hacker, User


class DevLoginTestCase(TestCase):
    @override_settings(DEV_LOGIN=False)
    def test_disabled_returns_404(self):
        response = self.client.post(reverse("dev_login"))
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(DEV_LOGIN=False)
    def test_login_page_has_no_dev_button_when_disabled(self):
        response = self.client.get("/login/")
        self.assertNotContains(response, "dev user")

    @override_settings(DEV_LOGIN=True)
    def test_login_page_has_dev_button_when_enabled(self):
        response = self.client.get("/login/")
        self.assertContains(response, reverse("dev_login"))

    @override_settings(DEV_LOGIN=True)
    def test_requires_post(self):
        response = self.client.get(reverse("dev_login"))
        self.assertEqual(response.status_code, 405)

    @override_settings(DEV_LOGIN=True)
    def test_logs_in_as_dev_superuser(self):
        response = self.client.post(reverse("dev_login"), follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=DEV_USERNAME)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)
        self.assertTrue(user.is_superuser)
        self.assertTrue(Hacker.objects.filter(user=user).exists())
        # Works on the pages that need a logged in user
        self.assertEqual(self.client.get(reverse("new")).status_code, 200)

    @override_settings(DEV_LOGIN=True)
    def test_login_twice_reuses_the_user(self):
        self.client.post(reverse("dev_login"))
        self.client.post(reverse("dev_login"))
        self.assertEqual(User.objects.filter(username=DEV_USERNAME).count(), 1)
