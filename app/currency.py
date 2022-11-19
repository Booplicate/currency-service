"""
Module that implements different currencies
"""

from __future__ import annotations


import abc
from decimal import Decimal
from typing import (
    TypeVar,
    ClassVar,
    TypeAlias
)
import functools
from types import MappingProxyType


MIN_AMOUNT = Decimal("0.0")

T = TypeVar("T", bound="BaseCurrency")
U = TypeVar("U", bound="BaseCurrency")
# Number: TypeAlias = Decimal | int | str | float

_currency_type_map: dict[str, type["BaseCurrency"]] = {}


class CurrencyError(Exception):
    """
    Base class for exceptions
    """
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __repr__(self) -> str:
        return f"{type(self).__name__}: '{self.msg}'"

class InvalidCurrencyValue(CurrencyError, ValueError):
    """
    Exception is raised on attempt to create a currency with invalid value
    """

class InvalidCurrencyOperation(CurrencyError, ArithmeticError):
    """
    Exception is raised on attempt to do an invalid operation on a currency
    """

class UnknownCurrency(CurrencyError, LookupError):
    """
    Exception is raised on attempt to access a currency that doesn't exist
    """

class InvalidExchangeRate(InvalidCurrencyValue):
    """
    Exception is raised on invalid exchange rate
    """

class MissingExchangeRate(UnknownCurrency):
    """
    Exception is raised on requiring a rate for a missing currency
    """


@functools.total_ordering
class BaseCurrency(abc.ABC):
    """
    ABC for currency classes
    """
    __NAME: ClassVar[str]

    __slots__ = ("__value",)

    def __init__(self, value: Decimal = MIN_AMOUNT) -> None:
        if not isinstance(value, Decimal):
            # value = Decimal(value)
            raise InvalidCurrencyValue("'value' must be an instance of 'Decimal'")

        if value < MIN_AMOUNT:
            raise InvalidCurrencyValue(f"'value' must be >= 0.0, got {value}")

        self.__value = value

    def __repr__(self) -> str:
        return f"<Currency('{self.get_name()}', {self.get_value()})>"

    @classmethod
    def __init_subclass__(cls: type[T], /, currency_name: str|None = None, **kwargs):
        """
        Controls subclassing, exists just so we can give a different name to the currency
        """
        super().__init_subclass__(**kwargs)

        name = (
            cls.__name__
            if currency_name is None
            else currency_name.upper()
        )

        if name in _currency_type_map:
            raise CurrencyError(f"Currency with name '{name}' already exists")

        cls.__NAME = name
        _currency_type_map[name] = cls

    @classmethod
    def get_type(cls: type[T]) -> type[T]:
        """
        Returns the type of this currency
        """
        return cls

    @classmethod
    def get_name(cls) -> str:
        """
        Returns the name of this currency
        """
        return cls.__NAME

    def get_value(self) -> Decimal:
        """
        Returns this currency's value
        """
        return self.__value

    def get_current_hash(self) -> int:
        """
        Method returns CURRENT hash of this mutable object,
        it can change over time and thus be used to compare if the object
        has changed over time
        """
        return hash((self.get_type(), self.get_name(), self.get_value()))

    def __eq__(self, other) -> bool:
        cls = type(self)
        if isinstance(other, cls):
            return self.get_value() == other.get_value()

        return NotImplemented

    def __lt__(self, other) -> bool:
        cls = type(self)
        if isinstance(other, cls):
            return self.get_value() < other.get_value()

        return NotImplemented

    def __le__(self, other) -> bool:
        cls = type(self)
        if isinstance(other, cls):
            return self.get_value() <= other.get_value()

        return NotImplemented

    def __add__(self: T, other) -> T:
        cls = type(self)
        if isinstance(other, cls):
            return cls(value=self.get_value() + other.get_value())

        return NotImplemented

    def __iadd__(self: T, other) -> T:
        if isinstance(other, type(self)):
            self.__value += other.get_value()
            return self

        return NotImplemented

    def __sub__(self: T, other) -> T:
        cls = type(self)
        if isinstance(other, cls):
            new_value = self.get_value() - other.get_value()
            if new_value < MIN_AMOUNT:
                raise InvalidCurrencyOperation(
                    "Subtrahend currency cannot be bigger than minuend currency"
                )

            return cls(value=new_value)

        return NotImplemented

    def __isub__(self: T, other) -> T:
        if isinstance(other, type(self)):
            if self.get_value() < other.get_value():
                raise InvalidCurrencyOperation(
                    "Subtrahend currency cannot be bigger than minuend currency"
                )

            self.__value -= other.get_value()
            return self

        return NotImplemented


def get_currency_type(name: str):
    """
    Returns a currency type by name
    """
    return _currency_type_map.get(name, None)

def get_currency_types():
    """
    Returns read-only mapping over currency types
    """
    return MappingProxyType(_currency_type_map)


class CurrencyManager():
    """
    Class represents a storage for currencies
    and allows managing them
    """
    __slots__ = ("__currencies",)

    def __init__(self, *currency_names: str) -> None:
        """
        Constructor

        IN:
            *currency_names - the ids of defined currency types
                that this manager will use/support
        """
        map_: dict[str, BaseCurrency] = {}
        for name in currency_names:
            currrency_type = get_currency_type(name)
            if currrency_type is None:
                raise UnknownCurrency(f"Unknown currency '{name}'")

            map_[name] = currrency_type()

        self.__currencies = map_

    def __repr__(self) -> str:
        return "<CurrencyManager({})>".format(
            ", ".join(map(str, self.__currencies.values()))
        )

    def _get_currency(self, currency_name: str) -> BaseCurrency:
        if (curr := self.__currencies.get(currency_name, None)) is None:
            raise UnknownCurrency(f"Unknown currency '{currency_name}'")

        return curr

    def _set_currency(self, curr: BaseCurrency):
        self.__currencies[curr.get_name()] = curr

    def get_all_balance(self) -> dict[str, Decimal]:
        """
        Returns a mapping {currency_name: current_balance} containing
        every currency
        """
        return {
            name: currency.get_value()
            for name, currency
            in self.__currencies.items()
        }

    def get_balance(self, currency_name: str) -> Decimal:
        """
        Returns balance for the given currency
        """
        return self._get_currency(currency_name).get_value()

    def add_balance(self, currency_name: str, value: Decimal):
        """
        Adds to balance for the given currency
        """
        if value <= MIN_AMOUNT:
            InvalidCurrencyValue(f"Invalid value for a currency {value}")

        curr = self._get_currency(currency_name)
        curr_type = curr.get_type()
        curr += curr_type(value)

    def remove_balance(self, currency_name: str, value: Decimal):
        """
        Removes from balance for the given currency
        """
        if value <= MIN_AMOUNT:
            InvalidCurrencyValue(f"Invalid value for a currency {value}")

        curr = self._get_currency(currency_name)
        curr_type = curr.get_type()
        other = curr_type(value)

        if curr < other:
            InvalidCurrencyOperation(f"Not enough '{currency_name}' for this operation")

        curr -= other

    def set_balance(self, currency_name: str, value: Decimal):
        """
        Sets balance for the given currency
        """
        if value < MIN_AMOUNT:
            InvalidCurrencyValue(f"Invalid value for a currency {value}")

        curr = self._get_currency(currency_name)
        curr_type = curr.get_type()
        self._set_currency(curr_type(value))

    def get_current_hash(self) -> int:
        """
        Returns current hash of this object,
        NOT to be used as a key for hashsets/hashmaps
        """
        # Preserve order
        currency_hashes = sorted(
            (name, curr.get_current_hash()) for name, curr in self.__currencies.items()
        )
        return hash(tuple(currency_hashes))


class CurrencyExchanger():
    """
    Represents a currency exchanger
    """
    __slots__ = (
        "__rates",
        "__base_currency"
    )

    def __init__(self, base_currency_name: str) -> None:
        """
        Constructor

        IN:
            base_currency_name - name of the currency we base the exchange rates
                of for other currencies
        """
        if base_currency_name not in get_currency_types():
            raise UnknownCurrency(
                f"Attempted to init CurrencyExchanger with unknown base currency '{base_currency_name}'"
            )

        self.__rates: dict[str, Decimal] = {}
        self.__base_currency = base_currency_name
        self.set_rate(base_currency_name, Decimal("1.0"))

    def __repr__(self) -> str:
        return "<CurrencyExchanger('{}', {})>".format(
            self.__base_currency,
            self.__rates
        )

    def set_rate(self, currency_name: str, rate: Decimal):
        """
        Adds exchange rate to this exchanger
        """
        if rate <= MIN_AMOUNT:
            raise InvalidExchangeRate(f"Exchange rate must be greater than 0, got {rate}")

        self.__rates[currency_name] = rate

    def set_rates(self, data: dict[str, Decimal]):
        """
        Adds multiple exchange rates for different currencies
        """
        for curr_name, rate in data.items():
            self.set_rate(curr_name, rate)

    def get_rate(self, currency_name: str) -> Decimal|None:
        """
        Returns exchange rate for a currency
        """
        return self.__rates.get(currency_name, None)

    def get_rate_unsafe(self, currency_name: str) -> Decimal:
        """
        Returns exchange rate for a currency
        Will raise exceptions on error
        """
        if (rate := self.get_rate(currency_name)) is None:
            raise MissingExchangeRate(f"No exchange rate for '{currency_name}'")

        return rate

    def get_cross_rate_unsafe(self, in_curr_name: str, out_curr_name: str) -> Decimal:
        """
        Returns exchange rate when converting in_curr_name into out_curr_name
        This will raise exceptions on error
        """
        return self.get_rate_unsafe(in_curr_name) / self.get_rate_unsafe(out_curr_name)

    def get_current_hash(self) -> int:
        """
        Returns current hash of this object,
        NOT to be used as a key for hashsets/hashmaps as
        this object is MUTABLE
        """
        # Always sort to prevent hash change due to ordering
        rates = sorted((k, v) for k, v in self.__rates.items())
        return hash(tuple(rates))

    def exchange(self, in_curr_name: str, value: Decimal, out_curr_name: str) -> Decimal:
        """
        Exchanges some currency using the current rate for it
        """
        if value < MIN_AMOUNT:
            raise InvalidCurrencyValue(f"Currency must be non-negative, got {value}")

        rate = self.get_cross_rate_unsafe(in_curr_name, out_curr_name)
        return value * rate


class RUB(BaseCurrency):
    pass

class USD(BaseCurrency):
    pass

class EUR(BaseCurrency, currency_name="EUR"):
    pass
