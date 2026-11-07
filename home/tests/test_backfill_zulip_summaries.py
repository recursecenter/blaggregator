from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from mock import patch

from home.tests.utils import PostFactory

MODULE = "home.management.commands.backfill_zulip_summaries"
ANNOUNCEMENT = "@**Someone** has a new blog post: [{title}](https://example.com/post/{slug}/view)"


def announcement(post, summary=""):
    content = ANNOUNCEMENT.format(title=post.title, slug=post.slug)
    return {"id": post.id + 1000, "content": content + summary}


class BackfillZulipSummariesTestCase(TestCase):
    def run_command(self, messages, *args, stream="--stream=blogging"):
        out = StringIO()
        with patch(f"{MODULE}.get_stream_messages", return_value=messages) as get, patch(
            f"{MODULE}.update_message_content", return_value=True
        ) as update:
            options = [stream] if stream else []
            call_command(
                "backfill_zulip_summaries", "--delay=0", *options, *args, stdout=out
            )
        self.get, self.update, self.out = get, update, out.getvalue()

    def test_dry_run_does_not_edit_messages(self):
        post = PostFactory(content="<p>Hello there</p>")
        message = announcement(post)
        self.run_command([message])
        self.update.assert_not_called()
        self.assertIn("Would update message", self.out)
        # The new content of the message is shown
        self.assertIn("    | " + message["content"], self.out)
        self.assertIn("    | ```quote\n    | Hello there\n    | ```", self.out)
        self.assertIn("1 to update", self.out)
        self.assertIn("dry run", self.out)

    def test_apply_appends_the_summary(self):
        post = PostFactory(content="<p>Hello there</p>")
        message = announcement(post)
        self.run_command([message], "--apply")
        self.update.assert_called_once_with(
            message["id"], message["content"] + "\n```quote\nHello there\n```"
        )
        self.assertIn("1 updated", self.out)
        self.assertNotIn("dry run", self.out)

    def test_messages_with_summaries_are_left_alone(self):
        post = PostFactory(content="<p>Hello there</p>")
        message = announcement(post, "\n```quote\nHello there\n```")
        self.run_command([message], "--apply")
        self.update.assert_not_called()
        self.assertIn("1 already have a summary", self.out)

    def test_posts_without_a_summary_are_left_alone(self):
        empty = PostFactory(content="")
        image = PostFactory(content="<p><img src='http://x/y.png'></p>")
        self.run_command([announcement(empty), announcement(image)], "--apply")
        self.update.assert_not_called()
        self.assertIn("2 have no summary", self.out)

    def test_other_messages_are_left_alone(self):
        known = PostFactory(content="<p>Hello</p>")
        unknown = {"id": 1, "content": "See https://example.com/post/zzzzzz/view"}
        other = {"id": 2, "content": "Just saying hi"}
        self.run_command([unknown, other, announcement(known)], "--apply")
        self.update.assert_called_once()
        self.assertIn("1 have no link to a post", self.out)
        self.assertIn("1 link to unknown posts", self.out)
        # Each skipped message is shown, so that it can be looked up
        self.assertIn("Skipping message 1, unknown post zzzzzz: See https://", self.out)
        self.assertIn("Skipping message 2, no link to a post: Just saying hi", self.out)

    def test_failures_are_counted_and_do_not_stop_the_rest(self):
        posts = [PostFactory(content="<p>Hello</p>") for _ in range(2)]
        out = StringIO()
        with patch(
            f"{MODULE}.get_stream_messages", return_value=[announcement(p) for p in posts]
        ), patch(f"{MODULE}.update_message_content", side_effect=[False, True]) as update:
            call_command(
                "backfill_zulip_summaries", "--stream=blogging", "--apply", "--delay=0", stdout=out
            )
        self.assertEqual(2, update.call_count)
        self.assertIn("1 updated, 1 failed", out.getvalue())
        self.assertIn("Could not update message", out.getvalue())

    def test_gets_raw_messages_we_sent_from_each_stream(self):
        self.run_command([], "--limit=50", stream=None)
        streams = [call.args[0] for call in self.get.call_args_list]
        self.assertEqual(["blogging", "Daily Logs"], streams)
        for call in self.get.call_args_list:
            self.assertTrue(call.kwargs["raw"])
            self.assertEqual(50, call.kwargs["limit"])
            self.assertIn("sender", call.kwargs)

    def test_streams_can_be_chosen(self):
        self.run_command([], "--stream=bot-test", stream=None)
        self.assertEqual(["bot-test"], [call.args[0] for call in self.get.call_args_list])

    def test_running_again_does_nothing(self):
        post = PostFactory(content="<p>Hello there</p>")
        message = announcement(post)
        self.run_command([message], "--apply")
        edited = {**message, "content": self.update.call_args.args[1]}
        self.run_command([edited], "--apply")
        self.update.assert_not_called()
