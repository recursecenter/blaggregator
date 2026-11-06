"""Fill the database with fake data. Only works in DEBUG mode."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from home.dev import DEV_USERNAME, get_dev_user
from home.models import Hacker, User


class Command(BaseCommand):
    help = "Create fake users, blogs and posts for local development."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5)
        parser.add_argument("--posts", type=int, default=8, help="Posts per user")

    def handle(self, users, posts, **options):
        if not settings.DEBUG or settings.DEPLOYED:
            raise CommandError("This only works with DJANGO_DEBUG set, locally.")

        # Test factories are a development dependency, so import them lazily.
        from home.tests.utils import BlogFactory, PostFactory, UserFactory

        dev_user = get_dev_user()
        if User.objects.exclude(id=dev_user.id).exists():
            self.stdout.write("Database already has data; not adding any.")
            return

        for user in [dev_user] + UserFactory.create_batch(users):
            Hacker.objects.get_or_create(user=user)
            blog = BlogFactory(user=user)
            PostFactory.create_batch(posts, blog=blog)

        self.stdout.write(
            "Created {} users with {} posts each.  Log in as {} using the dev "
            "login (DEV_LOGIN=1).".format(users + 1, posts, DEV_USERNAME)
        )
