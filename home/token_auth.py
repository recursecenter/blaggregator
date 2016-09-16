""" Define a new backend for authenticating with a token. """

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class TokenAuthBackend(ModelBackend):
    """ Allows users to authenticate using a token instead of username/password. """

    def authenticate(self, token):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(hacker__token=token)

        except UserModel.DoesNotExist:
            return None
