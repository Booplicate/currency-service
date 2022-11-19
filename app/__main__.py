"""
Entry point
"""

import argparse
import asyncio
import os
# import signal
from decimal import Decimal
from functools import partial

import app
from . import (
    api,
    currency,
    echo_server,
    fetcher,
    state,
    log_utils
)


# STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)

# TODO: Doing str.lower would be much better UX
TRUE_VALUES = frozenset(("1", "true", "True", "y", "Y"))
FALSE_VALUES = frozenset(("0", "false", "False", "n", "N"))
ALL_VALUES = TRUE_VALUES | FALSE_VALUES


def _get_bool_values() -> str:
    return ", ".join(map(lambda s: f"'{s}'", ALL_VALUES))

def _parse_debug(value: str) -> bool:
    if value in TRUE_VALUES:
        return True

    if value in FALSE_VALUES:
        return False

    raise ValueError(
        "Unknown value for the 'debug' parameter: '{}', supported values: {}".format(
            value,
            _get_bool_values()
        )
    )

def _parse_period(value: str) -> int:
    rv = int(value)
    if rv <= 0:
        raise ValueError(f"Period must be a positive integer, got {value}")
    return rv * 60

def parse_args() -> argparse.Namespace:
    """
    Processes program arguments, returns parsed data
    """
    parser = argparse.ArgumentParser(prog="app", description="launches service")
    # TODO: This should be a flag, not a parameter, but the specification says otherwise
    parser.add_argument(
        "--debug",
        type=_parse_debug,
        default="0",
        help=f"debug 'flag', allowed values: {_get_bool_values()}"
    )
    parser.add_argument(
        "--period",
        type=_parse_period,
        # default="1",
        required=True,# Specifications says require
        help="currency exchange rates update interval in minutes"
    )
    default_curr_val = currency.MIN_AMOUNT
    for curr_name in currency.get_currency_types().keys():
        parser.add_argument(
            f"--{curr_name.lower()}",
            type=Decimal,
            default=default_curr_val,
            help=f"starting amount of {curr_name}"
        )

    return parser.parse_args()



async def main():
    """
    Entry point
    """
    args = parse_args()

    if args.debug:
        os.environ["VERBOSE_LOGS"] = "1"

    log_utils.init()

    curr_names = tuple(currency.get_currency_types().keys())
    # Set requested "default" values
    manager = currency.CurrencyManager(*curr_names)
    for name in curr_names:
        if (start_amount := getattr(args, name.lower(), None)) is not None:
            manager.add_balance(name, start_amount)

    # Define app state
    app.app_state = state.State(
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
    log_utils.logger.info("SERVICE STARTING")
    try:
        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        # This is expected on exit
        pass

    finally:
        log_utils.logger.info("SERVICE STOPPING")
        log_utils.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
