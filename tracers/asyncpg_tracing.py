# https://github.com/condorcet/asyncpg-opentracing
from functools import wraps
from opentracing import tags, logs
from contextlib import contextmanager
from ddtrace import tracer
from ddtrace.ext import SpanTypes, http
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY


def operation_name(query: str):
    # TODO: some statement should contain two words. For example CREATE TABLE.
    query = query.strip().split(" ")[0].strip(";").upper()
    return "asyncpg " + query


@contextmanager
def con_context(handler, query, query_args):
    _tags = {
        tags.DATABASE_TYPE: "SQL",
        tags.DATABASE_STATEMENT: query,
        tags.DATABASE_USER: handler._params.user,
        tags.DATABASE_INSTANCE: handler._params.database,
        "db.params": query_args,
        tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
        ANALYTICS_SAMPLE_RATE_KEY: True,
    }
    child_span = tracer.current_span()
    with tracer.start_span(
        operation_name(query),
        child_of=child_span,
        span_type=SpanTypes.SQL,
        resource=operation_name(query),
        service="valuations-db",
    ) as span:
        span.set_tags(_tags)
        yield


def wrap(coro):
    @wraps(coro)
    async def wrapped(self, query, *args, **kwargs):
        with con_context(self, query, args):
            return await coro(self, query, *args, **kwargs)

    return wrapped


def wrap_executemany(coro):
    @wraps(coro)
    async def wrapped(self, query, args, *_args, **kwargs):
        with con_context(self, query, args):
            return await coro(self, query, args, *_args, **kwargs)

    return wrapped


def tracing_connection(cls):

    cls.fetch = wrap(cls.fetch)
    cls.fetchval = wrap(cls.fetchval)
    cls.fetchrow = wrap(cls.fetchrow)
    cls.execute = wrap(cls.execute)
    cls.executemany = wrap_executemany(cls.executemany)

    return cls
