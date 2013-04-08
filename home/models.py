from django.db import models
from django.contrib.auth.models import User

# extends the User class to hold additional profile info
# access with u.hacker.github (where u is user object instance)
class Hacker(models.Model):
    user = models.OneToOneField(User)
    avatar_url  = models.CharField(max_length=400)
    github      = models.CharField(max_length=200)
    twitter     = models.CharField(max_length=200)
    irc         = models.CharField(max_length=200)

class Blog(models.Model):

    def __unicode__(self):
        return self.feed_url

    feed_url     = models.CharField(max_length=200)
    # user         = models.ForeignKey(User)
    last_crawled = models.DateTimeField('last crawled')