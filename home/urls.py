from django.conf.urls import include, patterns, url
from django.http import HttpResponseRedirect

from home import views

urlpatterns = patterns('',
    url(r'^$', lambda x: HttpResponseRedirect('/new')),
    url(r'^login/$', views.log_in_oauth),
    # url(r'^login/$', views.log_in),
    # url(r'^log_in/$', views.log_in, name='log_in'),
    url(r'^create_account/$', views.create_account, name='create_account'),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^new/$', views.new, name='new'),
    url(r'^new/(?P<page>\d+)/$', views.new),
    url(r'^add_blog/$', views.add_blog, name='add_blog'),
    url(r'^atom\.xml/$', views.feed, name='feed'),
    url(r'^post/(?P<slug>\w+)/view', views.framed, name='framed'),
    url(r'^post/(?P<slug>\w+)/', views.item, name='post'),
    url(r'^logout/$', views.log_out),
    url(r'^log_out/$', views.log_out, name='log_out'),
    url(r'^about/$', views.about, name='about'),
    url(r'^complete/hackerschool/$', views.complete),
    url('', include('social.apps.django_app.urls', namespace='social')),
)
