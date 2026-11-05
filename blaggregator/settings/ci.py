DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "blaggregator_ci",  # Must match the service config in .github/workflows/ci.yml
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    }
}
