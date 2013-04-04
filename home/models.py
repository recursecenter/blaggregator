from django.db import models

class User(models.Model):

    def __unicode__(self):
        return self.email

    email       = models.CharField(max_length=200)
    avatar_url  = models.CharField(max_length=400)
    hs_id       = models.IntegerField(default=0)
    first_name  = models.CharField(max_length=200)
    last_name   = models.CharField(max_length=200)
    github      = models.CharField(max_length=200)
    twitter     = models.CharField(max_length=200)
    irc         = models.CharField(max_length=200)

