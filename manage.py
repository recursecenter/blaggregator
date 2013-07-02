#!/usr/bin/env python
import os
import sys
import blaggregator.settings.base as settings

sys.path.insert(0, settings.SITE_ROOT)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blaggregator.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
