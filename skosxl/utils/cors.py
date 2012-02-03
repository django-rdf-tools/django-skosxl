from django.conf import settings

#: By default we'll set CORS Allow Origin * for all application/json responses
DEFAULT_CORS_PATHS = (
    ('/', ('application/json', ), (('Access-Control-Allow-Origin', '*'), )),
    ('/', ('text/html', ), (('Access-Control-Allow-Origin', '*'), )),
    ('/', ('application/xhtml', ), (('Access-Control-Allow-Origin', '*'), )),
)

class CORSMiddleware(object):
    """
Middleware that serves up representations with a CORS header to
allow third parties to use your web api from JavaScript without
requiring them to proxy it.

See: http://www.w3.org/TR/cors/

Installation
------------

1. Add to ``settings.MIDDLEWARE_CLASSES``::

'sugar.middleware.cors.CORSMiddleware',

2. Optionally, configure ``settings.CORS_PATHS`` if the default settings
aren't appropriate for your application. ``CORS_PATHS`` should be a
list of (path, content_types, headers) values where content_types and
headers are lists of mime types and (key, value) pairs, respectively.

Processing occurs first to last so you should order ``CORS_PATHS``
items from most to least specific.

See ``DEFAULT_CORS_PATHS`` for an example.

Notes
-----

* Although not officially a feature, the headers are not restricted to
the CORS spec and could conceivably include other values such as
desired (allowing, for example, custom ``Cache-Control`` settings).
"""

    def __init__(self):
        self.paths = getattr(settings, "CORS_PATHS", DEFAULT_CORS_PATHS)

    def process_response(self, request, response):
        content_type = response.get('content-type', '').split(";")[0].lower()

        for path, types, headers in self.paths:
            if request.path.startswith(path) and content_type in types:
                for k, v in headers:
                    response[k] = v
                break
        return response