"""
Module implements logging utils for the app
"""

import logging
from logging import handlers
import os
import sys
import queue
from typing import Callable
from collections.abc import Awaitable

import fastapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette import concurrency


FMT = "[{asctime}] [{levelname}]: {message}"
DATEFMT = "%Y-%m-%d %H:%M:%S"

logger: logging.Logger
listener: handlers.QueueListener


def _should_log_extra() -> bool:
    return bool(os.environ.get("VERBOSE_LOGS", False))

def _get_app_log_level() -> int:
    if _should_log_extra():
        return logging.DEBUG

    return logging.INFO

def get_lib_log_level() -> int:
    if _should_log_extra():
        return logging.INFO

    return logging.WARNING

def init():
    """
    Initialises logging system
    """
    global logger, listener

    console_formatter = logging.Formatter(fmt=FMT, datefmt=DATEFMT, style="{")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)

    q = queue.Queue(-1)
    q_handler = handlers.QueueHandler(q)
    q_handler.setLevel(logging.DEBUG)

    listener = handlers.QueueListener(q, console_handler, respect_handler_level=True)

    logger = logging.getLogger("app")
    logger.setLevel(_get_app_log_level())
    logger.addHandler(q_handler)

    listener.start()

def shutdown():
    """
    Shuts down logging system
    """
    listener.stop()
    logging.shutdown()


async def log_request_content(request: fastapi.Request):
    """
    Dependency function to use in Router to enable
    logging request body
    """
    logger.debug(
        "Request: {} | '{}' | '{}' | {!r}".format(
            request.client,
            request.method,
            request.url,
            await request.body()
        )
    )

async def log_response_content(request: fastapi.Request, response: fastapi.Response):
    """
    Dependency function to use in Router to enable
    logging response content
    """
    content = []
    async for chunk in response.body_iterator:# type: ignore
        if not isinstance(chunk, bytes):
            chunk = chunk.encode(response.charset)
        content.append(chunk)

    logger.debug(
        "Response: {} | {} | {!r}".format(
            request.client,
            response.status_code,
            b"".join(content)
        )
    )
    # HACK: we exhausted the iterator and have to "refresh" it
    setattr(
        response,
        "body_iterator",
        concurrency.iterate_in_threadpool(iter(content))
    )

class ContentLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses contents
    """
    async def dispatch(
        self,
        request: fastapi.Request,
        call_next: Callable[[fastapi.Request], Awaitable[fastapi.Response]]
    ) -> fastapi.Response:
        # FIXME: See https://github.com/tiangolo/fastapi/issues/394
        # and https://github.com/encode/starlette/issues/495
        # on why this is impossible as of now
        # await log_request_content(request)

        response = await call_next(request)

        await log_response_content(request, response)

        return response
