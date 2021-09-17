from django import http


class RecurseSubdomainMiddleware(object):
    """Middleware to redirect all users to recurse subdomain."""

    HTTPS_REDIRECTS = {
        "blaggregator.us": "blaggregator.recurse.com",
        "www.blaggregator.us": "blaggregator.recurse.com",
    }

    def process_request(self, request):
        """Check for old HTTP_HOST and redirect to recurse subdomain."""

        host = request.get_host()
        if host in self.HTTPS_REDIRECTS:
            request.META["HTTP_HOST"] = self.HTTPS_REDIRECTS[host]
            newurl = request.build_absolute_uri().replace("http://", "https://")
            return http.HttpResponsePermanentRedirect(newurl)
