from opentracing.scope_managers.contextvars import ContextVarsScopeManager
from ddtrace.opentracer import Tracer, set_global_tracer
from sanic.response import HTTPResponse
from sanic.request import Request

from typing import List, AnyStr, Callable
from opentracing import tags
import opentracing
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY


def init_tracer(app_name, agent_hostname, agent_port):
    tracer = Tracer(
        app_name,
        config={"agent_hostname": agent_hostname, "agent_port": agent_port},
        scope_manager=ContextVarsScopeManager(),
    )
    set_global_tracer(tracer)
    return tracer


class SanicTracing:
    def __init__(self, tracer, app):
        self._tracer = tracer
        self._app = app
        self._current_scopes = {}

        @app.middleware("request")
        def on_request(request):
            self.process_request(request)

        @app.middleware("response")
        def on_response(request, response):
            self.process_response(request, response)

    def process_request(self, request: Request):
        operation_name = "web.request"
        headers = {}
        scope = self._tracer.start_active_span(operation_name)
        self._current_scopes[repr(request)] = scope

        span = scope.span
        span.set_tag("span.type", "web")
        span.set_tag(tags.COMPONENT, "Sanic")
        span.set_tag(tags.HTTP_METHOD, request.method)
        span.set_tag(tags.HTTP_URL, request.url)
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        span.set_tag(ANALYTICS_SAMPLE_RATE_KEY, True)

        return

    def process_response(self, request: Request, response: HTTPResponse):
        scope = self._current_scopes.pop(repr(request), None)
        if scope is None:
            return
        scope.span.set_tag("resource.name", f"{request.method} {request.uri_template}")
        if response is not None:
            scope.span.set_tag(tags.HTTP_STATUS_CODE, response.status)

        scope.close()
