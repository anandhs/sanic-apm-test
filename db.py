import asyncpg


pool = {}
async def register_db(db_config, connection_class, loop):
    pool['conn_pool'] = await asyncpg.create_pool(
        loop=loop, max_size=100, connection_class=connection_class, **db_config
    )

async def cleanup(loop):
    await pool.get('conn_pool').close()


def acquire():
    return pool.get('conn_pool').acquire()

async def run_query():
    async with acquire() as conn:
        query = "select 1  "
        result = await conn.fetch(query)
        return {"result": result}
