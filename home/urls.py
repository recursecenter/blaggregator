from django.conf.urls import patterns, url
from django.http import HttpResponseRedirect

from home import views

urlpatterns = patterns('',
    url(r'^$', lambda x: HttpResponseRedirect('/new')),
    url(r'^login/$', views.log_in),
    url(r'^log_in/$', views.log_in, name='log_in'),
    url(r'^create_account/$', views.create_account, name='create_account'),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^new/$', views.new, name='new'),
    url(r'^add_blog/$', views.add_blog),
    url(r'^atom\.xml/$', views.feed, name='feed'),
    url(r'^submit_post/$', views.submit_post),
    url(r'^submitted_posts/$', views.submitted_posts),
    url(r'^all_posts/$', views.all_posts),
)
