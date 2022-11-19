"""
Module implements logging utils for the app
"""

import logging
from logging import handlers
import os
import sys
import queue

import fastapi


FMT = "[{asctime}] [{levelname}]: {message}"
DATEFMT = "%Y-%m-%d %H:%M:%S"

logger: logging.Logger
listener: handlers.QueueListener


def get_log_level():
    if os.environ.get("DEBUG", False):
        return logging.DEBUG

    return logging.INFO

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

    logger = logging.getLogger(__name__)
    logger.setLevel(get_log_level())
    logger.addHandler(q_handler)

    listener.start()

def shutdown():
    """
    Shuts down logging system
    """
    listener.stop()
    logging.shutdown()


async def log_request_content(request: fastapi.Request):
    pass

async def log_response_content(response: fastapi.Response):
    pass
