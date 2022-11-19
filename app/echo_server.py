"""
Module implements echo server for stdout
"""

import asyncio

import app
from . import log_utils


async def start_server(period: int):
    """
    Starts a coro that prints currency reports to stdout every period minutes
    """
    period = period * 60
    last_hash = app.app_state.get_current_hash()
    while True:
        new_hash = app.app_state.get_current_hash()
        if last_hash != new_hash:
            last_hash = new_hash
            report = await app.app_state.generate_report()
            log_utils.logger.info(f"Currency report:\n{report}")

        await asyncio.sleep(period)
