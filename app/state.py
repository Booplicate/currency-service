"""
Module that implements app state
"""

import asyncio
from decimal import Decimal

from app import log_utils

from . import currency
# just to meet the specifications
from .currency import BaseCurrency# pylint: disable=unused-import


class State():
    """
    Represents a state of this app
    ASYNC-SAFE (except few sync methods)
    THREAD-UNSAFE
    """
    def __init__(
        self,
        exchanger: currency.CurrencyExchanger,
        manager: currency.CurrencyManager
    ):
        """
        App state constructor

        IN:
            exchanger - currency exchanger to use
            manager - manager for currency management
        """
        self._lock = asyncio.Lock()
        self._exchanger = exchanger
        self._manager = manager

    def __repr__(self) -> str:
        return "<State({}, {})>".format(
            self._exchanger,
            self._manager
        )

    def get_current_hash(self) -> int:
        """
        Method returns current hash of this mutable object,
        NOT to be used as a key for hashsets/hashmaps
        """
        man_hash = self._manager.get_current_hash()
        ex_hash = self._exchanger.get_current_hash()
        return hash((man_hash, ex_hash))

    async def get_balance(self, currency_name: str) -> Decimal:
        """
        Returns balance for the given currency type
        """
        async with self._lock:
            return self._manager.get_balance(currency_name)

    async def get_all_balance(self) -> dict[str, Decimal]:
        """
        Returns a mapping with balance for each currency
        """
        async with self._lock:
            return self._manager.get_all_balance()

    async def set_balance(self, currency_name: str, value: Decimal):
        """
        Sets currency balance
        """
        async with self._lock:
            self._manager.set_balance(currency_name, value)

    async def set_balance_multi(self, **data: Decimal):
        """
        Sets balance for multiple currencies
        """
        async with self._lock:
            for currency_name, value in data.items():
                self._manager.set_balance(currency_name, value)

    async def add_balance(self, currency_name: str, value: Decimal):
        """
        Adds to currency balance if it exists
        """
        async with self._lock:
            self._manager.add_balance(currency_name, value)

    async def add_balance_multi(self, **data: Decimal):
        """
        Adds to balance of multiple currencies
        """
        async with self._lock:
            for currency_name, value in data.items():
                self._manager.add_balance(currency_name, value)

    async def remove_balance(self, currency_name: str, value: Decimal):
        """
        Removes currency balance if it exists
        """
        async with self._lock:
            self._manager.remove_balance(currency_name, value)

    async def remove_balance_multi(self, **data: Decimal):
        """
        Removes balance of multiple currencies
        """
        async with self._lock:
            for currency_name, value in data.items():
                self._manager.remove_balance(currency_name, value)

    async def set_exchange_rates(self, **data: Decimal):
        """
        Sets exchange rates
        """
        async with self._lock:
            self._exchanger.set_rates(data)

    async def calculate_exchange(
        self,
        in_curr_name: str,
        value: Decimal,
        out_curr_name: str
    ) -> Decimal:
        """
        Calculates exchange result and returns it
        """
        async with self._lock:
            return self._exchanger.exchange(in_curr_name, value, out_curr_name)

    def _generate_report(self) -> str:
        """
        Generates currency report as specified in the specifications
        """
        strings = []

        balance_data = self._manager.get_all_balance()
        for k, v in balance_data.items():
            strings.append(f"{k.lower()}: {v}\n")

        strings.append("\n")

        rates = self._exchanger.get_all_cross_rate()
        for k, v in rates.items():# type: ignore
            strings.append(f"{k[0].lower()}-{k[1].lower()}: {v}\n")

        strings.append("\n")

        strings.append("sum:")
        for i, (k, v) in enumerate(balance_data.items()):
            for kk, vv in balance_data.items():
                if k == kk:
                    continue

                try:
                    v += self._exchanger.exchange(kk, vv, k)

                except currency.MissingExchangeRate as e:
                    # We don't want the report to fail, rather just ignore the data
                    # we can't generate
                    # The only way this can happen is if we have currency, but no exchange rate for it
                    # (e.g. the service for that failed to send it to us)
                    log_utils.logger.error(
                        "Error while generating report, "
                        f"perhaps currency exchange rates are incomplete: {e}"
                    )

            strings.append(f" {v} {k.lower()}")

            if i != len(balance_data)-1:
                strings.append(" /")

        return "".join(strings)

    async def generate_report(self) -> str:
        """
        Generates currency report as specified in the specifications
        """
        async with self._lock:
            return self._generate_report()
