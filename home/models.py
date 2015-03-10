from django.db import models
from django.contrib.auth.models import User
import random, string

def generate_random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(6))

STREAM_CHOICES = (
    ('BLOGGING', 'blogging'),
    ('LOGS', 'Daily Logs'),
)

# extends the User class to hold additional profile info
# access with u.hacker.github (where u is user object instance)
class Hacker(models.Model):
    user = models.OneToOneField(User)
    avatar_url  = models.TextField(blank=True)
    github      = models.TextField(blank=True)
    twitter     = models.TextField(blank=True)

class Blog(models.Model):

    def __unicode__(self):
        return self.feed_url

    user         = models.ForeignKey(User)
    url          = models.URLField()
    feed_url     = models.URLField()
    last_crawled = models.DateTimeField('last crawled', blank=True, null=True)
    created      = models.DateTimeField('date created')
    stream       = models.CharField(max_length=100, default=STREAM_CHOICES[0][0], choices=STREAM_CHOICES)

class Post(models.Model):

    def __unicode__(self):
        return self.title

    blog         = models.ForeignKey(Blog)
    url          = models.TextField()
    title        = models.TextField(blank=True)
    content      = models.TextField()
    date_updated = models.DateTimeField('date updated')
    slug         = models.CharField(max_length=6, default=generate_random_id, unique=True)

class LogEntry(models.Model):

    def __unicode__(self):
        return "%s %s" % (self.date, self.post)

    post = models.ForeignKey(Post)

    date = models.DateTimeField()
    referer = models.URLField(blank=True, null=True)
    remote_addr = models.IPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
