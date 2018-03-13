# HACK: Tests fail with ImportError: cannot import name range This is probably
# because of some six madness between one of the test dependencies and django's
# internal six stuff.
from django.contrib.staticfiles.storage import staticfiles_storage  # noqa
