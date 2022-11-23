
import asyncio
import os
# import signal
from functools import partial

from . import (
    api,
    arg_parser,
    currency,
    echo_server,
    fetcher,
    state,
    log_utils
)


__author__ = "Booplicate"
__version__ = "0.1.0"


# quit_event = asyncio.Event()
# STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)
app_state: state.State


def is_debug_mode() -> bool:
    return bool(os.environ.get("CSA_DEBUG_MODE", False))

async def main():
    """
    Entry point
    """
    global app_state

    args = arg_parser.parse_args()

    if args.debug:
        os.environ["CSA_DEBUG_MODE"] = "1"

    log_utils.init()

    curr_names = tuple(currency.get_currency_types().keys())
    # Set requested "default" values
    manager = currency.CurrencyManager(*curr_names)
    for name in curr_names:
        if (start_amount := getattr(args, name.lower(), None)) is not None:
            manager.add_balance(name, start_amount)

    # Define app state
    app_state = state.State(
        currency.CurrencyExchanger("RUB"),
        manager
    )

    # Define our tasks
    api_server_task = asyncio.create_task(api.start_server(), name="api_server")
    rates_fetcher_task = asyncio.create_task(
        fetcher.start_currency_fetcher(
            fetcher.URL_CBR_XML_DAILY,
            fetcher.DataScheme_CBRXMLDaily,
            args.period
        ),
        name="rates_fetcher"
    )
    echo_server_task = asyncio.create_task(echo_server.start_server(1), name="echo_server")

    tasks = (
        api_server_task,
        rates_fetcher_task,
        echo_server_task
    )

    # Set exit callback
    def exit_callback(tasks_to_cancel):
        for task in tasks_to_cancel:
            task.cancel()
    api.add_quit_callback(
        partial(exit_callback, tasks[1:])
    )

    # Start
    if not args.debug:
        log_utils.logger.info("SERVICE STARTING")
    try:
        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        # This is expected on exit
        pass

    finally:
        # if not args.debug:
        #     log_utils.logger.info("SERVICE STOPPING")
        log_utils.shutdown()
