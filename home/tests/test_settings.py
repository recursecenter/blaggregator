import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from blaggregator.settings import base

NAME = "BLAGGREGATOR_TEST_CREDENTIAL"


class RecurseCredentialTestCase(SimpleTestCase):
    def test_returns_value_from_environment(self):
        with mock.patch.dict(os.environ, {NAME: "secret"}):
            self.assertEqual(base.recurse_credential(NAME), "secret")

    def test_missing_credential_is_empty_when_not_deployed(self):
        with mock.patch.object(base, "DEPLOYED", False):
            self.assertEqual(base.recurse_credential(NAME), "")

    def test_missing_credential_is_an_error_when_deployed(self):
        with mock.patch.object(base, "DEPLOYED", True):
            with self.assertRaises(ImproperlyConfigured):
                base.recurse_credential(NAME)

    def test_value_from_environment_is_used_when_deployed(self):
        with mock.patch.object(base, "DEPLOYED", True):
            with mock.patch.dict(os.environ, {NAME: "secret"}):
                self.assertEqual(base.recurse_credential(NAME), "secret")
