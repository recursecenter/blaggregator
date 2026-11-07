import json

from django.test import SimpleTestCase
from mock import Mock, patch

from home.zulip_helpers import delete_message, get_stream_messages, update_message_content


def response(data):
    return Mock(json=Mock(return_value=data))


@patch("home.zulip_helpers.requests")
class GetStreamMessagesTestCase(SimpleTestCase):
    def params(self, requests):
        return requests.get.call_args.kwargs["params"]

    def test_returns_messages(self, requests):
        messages = [{"id": 1}, {"id": 2}]
        requests.get.return_value = response({"result": "success", "messages": messages})
        self.assertEqual(messages, get_stream_messages("blogging"))

    def test_gets_the_newest_messages_by_default(self, requests):
        requests.get.return_value = response({"result": "success", "messages": []})
        get_stream_messages("blogging")
        params = self.params(requests)
        self.assertEqual("newest", params["anchor"])
        self.assertEqual(5000, params["num_before"])
        self.assertEqual(0, params["num_after"])
        self.assertEqual(
            [{"operator": "stream", "operand": "blogging"}], json.loads(params["narrow"])
        )

    def test_filters_by_sender_on_the_server(self, requests):
        requests.get.return_value = response({"result": "success", "messages": []})
        get_stream_messages("blogging", sender="bot@example.com")
        narrow = json.loads(self.params(requests)["narrow"])
        self.assertIn({"operator": "sender", "operand": "bot@example.com"}, narrow)

    def test_rendered_content_is_the_default(self, requests):
        requests.get.return_value = response({"result": "success", "messages": []})
        get_stream_messages("blogging")
        self.assertEqual("true", self.params(requests)["apply_markdown"])

    def test_raw_content(self, requests):
        requests.get.return_value = response({"result": "success", "messages": []})
        get_stream_messages("blogging", raw=True, limit=10)
        params = self.params(requests)
        self.assertEqual("false", params["apply_markdown"])
        self.assertEqual(10, params["num_before"])

    def test_api_errors_give_no_messages(self, requests):
        requests.get.return_value = response({"result": "error", "msg": "Bad stream"})
        self.assertEqual([], get_stream_messages("nope"))

    def test_network_errors_give_no_messages(self, requests):
        requests.get.side_effect = OSError("down")
        self.assertEqual([], get_stream_messages("blogging"))


@patch("home.zulip_helpers.requests")
class DeleteMessageTestCase(SimpleTestCase):
    def test_success(self, requests):
        requests.patch.return_value = response({"result": "success"})
        self.assertTrue(delete_message(5, "(gone)"))
        data = requests.patch.call_args.kwargs["data"]
        self.assertEqual({"content": "(gone)", "subject": "(gone)"}, data)
        self.assertTrue(requests.patch.call_args.args[0].endswith("/5"))

    def test_success_is_not_logged_as_an_error(self, requests):
        requests.patch.return_value = response({"result": "success"})
        with self.assertNoLogs("blaggregator", level="ERROR"):
            delete_message(5)

    def test_api_error(self, requests):
        requests.patch.return_value = response({"result": "error", "msg": "Too old"})
        with self.assertLogs("blaggregator", level="ERROR") as logs:
            self.assertFalse(delete_message(5))
        self.assertIn("Too old", logs.output[0])


@patch("home.zulip_helpers.requests")
class UpdateMessageContentTestCase(SimpleTestCase):
    def test_only_the_content_is_changed(self, requests):
        requests.patch.return_value = response({"result": "success"})
        self.assertTrue(update_message_content(7, "new **content**"))
        self.assertEqual({"content": "new **content**"}, requests.patch.call_args.kwargs["data"])
        self.assertTrue(requests.patch.call_args.args[0].endswith("/7"))

    def test_api_error(self, requests):
        requests.patch.return_value = response({"result": "error", "msg": "Too old"})
        with self.assertLogs("blaggregator", level="ERROR") as logs:
            self.assertFalse(update_message_content(7, "new"))
        self.assertIn("Too old", logs.output[0])
