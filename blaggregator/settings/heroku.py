import dj_database_url
from .base import DATABASES, STORAGES

# Parse database configuration from $DATABASE_URL
DATABASES["default"] = dj_database_url.config()
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Static files are served by WhiteNoise, with compression and hashed filenames.
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
