from django import http


class RecurseSubdomainMiddleware:
    """Middleware to redirect all users to recurse subdomain."""

    HTTPS_REDIRECTS = {
        "blaggregator.us": "blaggregator.recurse.com",
        "www.blaggregator.us": "blaggregator.recurse.com",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Check for old HTTP_HOST and redirect to recurse subdomain."""

        host = request.get_host()
        if host in self.HTTPS_REDIRECTS:
            request.META["HTTP_HOST"] = self.HTTPS_REDIRECTS[host]
            newurl = request.build_absolute_uri().replace("http://", "https://")
            return http.HttpResponsePermanentRedirect(newurl)

        return self.get_response(request)
