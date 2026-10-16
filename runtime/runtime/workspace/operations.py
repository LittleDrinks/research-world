import asyncio


async def settle(operation):
    task=asyncio.ensure_future(operation)
    cancelled=False
    while not task.done():
        try:await asyncio.shield(task)
        except asyncio.CancelledError:cancelled=True
    if cancelled:
        if not task.cancelled():task.exception()
        raise asyncio.CancelledError
    return task.result()
