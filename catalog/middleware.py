import logging
import time

# Logger for this app; output is configured in settings.LOGGING
logger = logging.getLogger("catalog")

# Requests for these paths are not logged (static files flood the terminal)
SKIP_PREFIXES = ("/static/", "/media/", "/favicon.ico")

# Requests slower than this many milliseconds get flagged as SLOW
SLOW_MS = 500


# === REQUEST LOGGING MIDDLEWARE ===
# Logs every request as aligned columns: method, status, time, path, user.
class RequestLoggingMiddleware:
    # Django calls this once at startup and passes in the next layer of the stack
    def __init__(self, get_response):
        self.get_response = get_response

    # Runs on every request: time the view, then log the result
    def __call__(self, request):
        # Skip noisy asset requests entirely
        if request.path.startswith(SKIP_PREFIXES):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        # "anonymous" when nobody is logged in
        user = request.user.username if request.user.is_authenticated else "anonymous"
        args = (request.method, response.status_code, elapsed_ms, request.path, user)

        # Fixed-width columns so lines stack neatly; slow requests log as warnings
        if elapsed_ms > SLOW_MS:
            logger.warning("%-5s %3d %5.0fms  %-20s %s   SLOW", *args)
        else:
            logger.info("%-5s %3d %5.0fms  %-20s %s", *args)
        return response
