from .base import DATABASES

# Same database, user and password as base.py; only the host differs.
DATABASES = {"default": {**DATABASES["default"], "HOST": "db"}}
