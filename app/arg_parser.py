"""
Module implements arg parser for the program
"""

import argparse
from decimal import Decimal

from . import currency


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
