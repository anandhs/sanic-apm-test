from asyncpg.connection import Connection
from tracers.asyncpg_tracing import tracing_connection


@tracing_connection
class TracingConnection(Connection):
    pass
