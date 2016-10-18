'''
   Assigns every comment a unique slug that is randomly generated.
   Only really useful for one-time migration to this new schema.
'''

from django.core.management.base import NoArgsCommand
from home.models import Comment
import random
import string


class Command(NoArgsCommand):

    help = 'One-time script to set unique ID\'s for all comments in database.'

    def handle_noargs(self, **options):

        if 'YES' == raw_input('\nDANGER DANGER DANGER.\nThis will overwrite slugs for all comments in the database. Type YES if you want to continue. '):
            for comment in Comment.objects.all():
                comment.slug = generate_random_id()
                comment.save()
                print "%s: %s" % (comment.slug, comment.content[:40])

        else:
            print "OK, quitting without doing anything."


def generate_random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(6))
