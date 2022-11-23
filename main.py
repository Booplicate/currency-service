"""
Extra entry point to run the program w/o the -m flag
"""

import asyncio

import app


if __name__ == "__main__":
    asyncio.run(app.main())
