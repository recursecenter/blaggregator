from django.conf import settings
from django.views.static import serve
from django.urls import include, path, re_path

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
]

if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]
