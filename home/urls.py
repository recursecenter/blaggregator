from django.conf.urls import include, patterns, url
from django.http import HttpResponseRedirect

from home import views

urlpatterns = patterns('',
    url(r'^$', lambda x: HttpResponseRedirect('/new')),
    url(r'^login/$', views.log_in_oauth),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^new/$', views.new, name='new'),
    url(r'^new/(?P<page>\d+)/$', views.new),
    url(r'^add_blog/$', views.add_blog, name='add_blog'),
    url(r'^edit_blog/(?P<blog_id>\d+)/$', views.edit_blog, name='edit_blog'),
    url(r'^delete_blog/(?P<blog_id>\d+)/$', views.delete_blog, name='delete_blog'),
    url(r'^feed/$', views.feed, name='feed'),
    url(r'^refresh_token/$', views.refresh_token, name='refresh_token'),
    url(r'^post/(?P<slug>\w+)/view', views.view_post, name='view_post'),
    url(r'^post/(?P<slug>\w+)/', views.item, name='post'),
    url(r'^logout/$', views.log_out),
    url(r'^log_out/$', views.log_out, name='log_out'),
    url(r'^login-error/$', views.login_error, name='login_error'),
    url(r'^about/$', views.about, name='about'),
    url(r'^updated_avatar/(?P<user_id>\d+)/$', views.updated_avatar, name='updated_avatar'),
    url('', include('social.apps.django_app.urls', namespace='social')),
)
