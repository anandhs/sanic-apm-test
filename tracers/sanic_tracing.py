# https://github.com/itechub/sanic-opentracing
from functools import wraps
from inspect import isawaitable
from typing import List, AnyStr, Callable

from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.request import Request
from ddtrace import tracer
from ddtrace.ext import SpanTypes, http
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY


def init_tracer(app, app_config=None):
    SERVICE_NAME = app_config.get('apm_service_name')

    @app.middleware("request")
    def on_request(request):
        span = tracer.trace(
            "web.request", span_type=SpanTypes.WEB, service=SERVICE_NAME
        )
        span.set_tag(http.METHOD, request.method)
        span.set_tag(http.URL, request.url)
        span.set_tag(http.QUERY_STRING, request.query_string)
        span.set_tag(ANALYTICS_SAMPLE_RATE_KEY, True)

    @app.middleware("response")
    def on_response(request, response):
        span = tracer.current_span()

        # span.resource is the url pattern that is displayed under APM -> SERVICES -> ENDPOINT
        span.resource = request.uri_template
        span.set_tag(http.STATUS_CODE, response.status)

        span.finish()
