'''
   One-time use: a bunch of avatar links are wrong. This script updates them locally.
'''

from django.core.management.base import NoArgsCommand
from home.models import Hacker
from django.core.exceptions import ObjectDoesNotExist

PREFIX = "https://www.hackerschool.com/assets/people/"

# FIXME: dictionary of { id: "url.jpg" } goes here
slugs = {}


class Command(NoArgsCommand):

    help = 'One-time script to update all avatar URLs for winter batch.'

    def handle_noargs(self, **options):

        if 'YES' == raw_input('\nDANGER DANGER DANGER.\nThis will overwrite all avatar URLs. Type YES if you want to continue. '):
            for id in slugs.keys():
                try:
                    hacker = Hacker.objects.get(user=id)
                    hacker.avatar_url = PREFIX + slugs[id]
                    hacker.save()
                    print "Found user %s" % Hacker.objects.get(user=id).avatar_url
                    # print "Would change user %s." % hacker.avatar_url
                except ObjectDoesNotExist:
                    print "Did NOT find user: %s" % slugs[id]

        else:
            print "OK, quitting without doing anything."
