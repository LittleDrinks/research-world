import os

import uvicorn

from .app import create_app


def main():
    port = int(os.environ.get("HARNESS_PORT", "8098"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
