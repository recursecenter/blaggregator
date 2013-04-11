from django.db import models
from django.contrib.auth.models import User

# extends the User class to hold additional profile info
# access with u.hacker.github (where u is user object instance)
class Hacker(models.Model):
    user = models.OneToOneField(User)
    avatar_url  = models.CharField(max_length=400, blank=True)
    github      = models.CharField(max_length=200, blank=True)
    twitter     = models.CharField(max_length=200, blank=True)
    irc         = models.CharField(max_length=200, blank=True)

class Blog(models.Model):

    def __unicode__(self):
        return self.feed_url

    user         = models.ForeignKey(User)
    url          = models.CharField(max_length=200)
    feed_url     = models.CharField(max_length=200)
    last_crawled = models.DateTimeField('last crawled', blank=True, null=True)
    created      = models.DateTimeField('date created')