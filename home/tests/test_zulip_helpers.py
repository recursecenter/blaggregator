from django.test import SimpleTestCase
from mock import Mock, patch

from home.zulip_helpers import delete_message


def response(data):
    return Mock(json=Mock(return_value=data))


@patch("home.zulip_helpers.requests")
class DeleteMessageTestCase(SimpleTestCase):
    def test_success(self, requests):
        requests.patch.return_value = response({"result": "success"})
        self.assertTrue(delete_message(5, "(gone)"))
        params = requests.patch.call_args.kwargs["params"]
        self.assertEqual({"content": "(gone)", "subject": "(gone)"}, params)
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
