import asyncio
import os
from pathlib import Path

from .adapter.pi import PiAdapter
from .bridge import ToolBridge
from .runtime import Runtime
from .server import serve


async def main():
    adapter = PiAdapter.detect()
    adapter.bridge = ToolBridge()
    runtime = Runtime(Path(os.getenv('RUNTIME_DATA', '/runtime-data')) / 'runs', {'pi': adapter})
    adapter.bridge.runtime = runtime
    try:
        await serve(runtime, adapter.bridge)
    finally:
        await runtime.close()


asyncio.run(main())
