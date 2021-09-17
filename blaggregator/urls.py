from django.conf.urls import include, url
from django.conf import settings
from django.views.static import serve

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'blaggregator.views.home', name='home'),
    # url(r'^blaggregator/', include('blaggregator.foo.urls')),
    # url(r'^profile/', include('home.urls')),
    url(r"^", include("home.urls")),
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r"^admin/", include(admin.site.urls)),
]

if not settings.DEBUG:
    urlpatterns += [
        url(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]
