from django.http import HttpResponseRedirect
from django.urls import include, path, re_path, reverse

from home import views

urlpatterns = [
    re_path(r"^$", lambda x: HttpResponseRedirect(reverse("new"))),
    re_path(r"^login/$", views.log_in_oauth),
    re_path(r"^profile/$", views.own_profile),
    re_path(r"^profile/(?P<user_id>\d+)/$", views.profile, name="profile"),
    re_path(r"^new/$", views.new, name="new"),
    re_path(r"^add_blog/$", views.add_blog, name="add_blog"),
    re_path(r"^edit_blog/(?P<blog_id>\d+)/$", views.edit_blog, name="edit_blog"),
    re_path(r"^delete_blog/(?P<blog_id>\d+)/$", views.delete_blog, name="delete_blog"),
    re_path(r"^atom\.xml$", views.feed, name="feed"),
    re_path(r"^refresh_token/$", views.refresh_token, name="refresh_token"),
    re_path(r"^post/(?P<slug>\w+)/view", views.view_post, name="view_post"),
    re_path(r"^logout/$", views.log_out),
    re_path(r"^log_out/$", views.log_out, name="log_out"),
    re_path(r"^login-error/$", views.login_error, name="login_error"),
    re_path(r"^about/$", views.about, name="about"),
    re_path(r"^most_viewed/$", views.most_viewed, name="most_viewed"),
    re_path(r"^most_viewed/(?P<ndays>\d+)/$", views.most_viewed, name="most_viewed_days"),
    re_path(r"^updated_avatar/(?P<user_id>\d+)/$", views.updated_avatar, name="updated_avatar"),
    re_path(r"^search/$", views.search, name="search"),
    path("", include("social_django.urls", namespace="social")),
]
