import logging
import time

# Logger for this app; output is configured in settings.LOGGING
logger = logging.getLogger("catalog")


# === REQUEST LOGGING MIDDLEWARE ===
# Logs every request's method, path, status code, user, and how long it took.
class RequestLoggingMiddleware:
    # Django calls this once at startup and passes in the next layer of the stack
    def __init__(self, get_response):
        self.get_response = get_response

    # Runs on every request: time the view, then log the result
    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        # "anonymous" when nobody is logged in
        user = request.user.username if request.user.is_authenticated else "anonymous"
        logger.info(
            "%s %s -> %s (%.0f ms) user=%s",
            request.method, request.path, response.status_code, elapsed_ms, user,
        )
        return response
