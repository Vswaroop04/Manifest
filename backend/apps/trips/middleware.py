import logging
from collections.abc import Callable
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("app")


def RequestLoggingMiddleware(get_response: Callable[[HttpRequest], HttpResponse]) -> Callable[[HttpRequest], HttpResponse]:
    def middleware(request: HttpRequest) -> HttpResponse:
        response = get_response(request)
        logger.info("%s %s %s", request.method, request.path, response.status_code)
        return response

    return middleware
