from django.conf.urls import patterns, url

from home import views

urlpatterns = patterns('',
    url(r'^log_in/', views.log_in, name='log_in'),
    url(r'^create_account', views.create_account, name='create_account'),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^new/', views.new, name='new'),
)