"""
Modules implements base API backend
"""

from typing import Callable

import fastapi

from . import endpoints
from .. import log_utils


app = fastapi.FastAPI()

app.include_router(endpoints.router)

app.add_middleware(log_utils.ContentLoggerMiddleware)


def add_quit_callback(fn: Callable):
    """
    Adds quit callback to run on shutdown
    """
    app.add_event_handler("shutdown", fn)
