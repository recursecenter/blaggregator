from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from home.models import Blog, Hacker, Post, User


class SeedDevDataTestCase(TestCase):
    def run_command(self, *args):
        out = StringIO()
        call_command("seed_dev_data", *args, stdout=out)
        return out.getvalue()

    def test_refuses_to_run_without_debug(self):
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(User.objects.exists())

    @override_settings(DEBUG=True, DEPLOYED=True)
    def test_refuses_to_run_on_deployed_servers(self):
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(User.objects.exists())

    @override_settings(DEBUG=True)
    def test_creates_users_blogs_and_posts(self):
        self.run_command("--users", "2", "--posts", "3")
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Hacker.objects.count(), 2)
        self.assertEqual(Blog.objects.count(), 2)
        self.assertEqual(Post.objects.count(), 6)

    @override_settings(DEBUG=True)
    def test_does_not_add_data_twice(self):
        self.run_command("--users", "1", "--posts", "1")
        self.run_command("--users", "1", "--posts", "1")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 1)
