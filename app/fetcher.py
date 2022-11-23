"""
Module that implements data fetcher
"""

import asyncio
import datetime
from decimal import Decimal
from json import JSONDecodeError
from typing import TypeVar
from collections.abc import AsyncIterator

import aiohttp
import pydantic

import app
from . import (
    currency,
    log_utils
)


V = TypeVar("V", bound=pydantic.BaseModel)# pylint: disable=no-member

URL_CBR_XML_DAILY = "https://www.cbr-xml-daily.ru/daily_json.js"


class _ValuteItemScheme_CBRXMLDaily(pydantic.BaseModel):# pylint: disable=no-member
    ID: str
    NumCode: str
    CharCode: str
    Nominal: Decimal
    Name: str
    Value: Decimal
    Previous: Decimal

class DataScheme_CBRXMLDaily(pydantic.BaseModel):# pylint: disable=no-member
    Date: datetime.datetime
    PreviousDate: datetime.datetime
    PreviousURL: str
    Timestamp: datetime.datetime
    Valute: dict[str, _ValuteItemScheme_CBRXMLDaily]


async def _fetch(url: str, period: int, timeout: int) -> AsyncIterator[dict]:
    """
    Continuously fetches json data from the given url every period seconds
    """
    timeout = aiohttp.ClientTimeout(timeout)# type: ignore
    async with aiohttp.ClientSession(timeout=timeout) as sesh:
        while True:
            async with sesh.get(url) as resp:
                try:
                    raw_data = await resp.json(content_type=None)
                    yield raw_data

                except (
                    JSONDecodeError,
                    aiohttp.ContentTypeError,
                    aiohttp.ServerTimeoutError
                ) as e:
                    log_utils.logger.error(
                        f"Failed to fetch data: {e}", exc_info=True
                    )

            await asyncio.sleep(period)

def _validate(raw_data: dict, scheme_type: type[V]) -> V|None:
    """
    Validates raw json vs Padantic schema, returns parsed model or None
    """
    try:
        data = scheme_type(**raw_data)

    except pydantic.ValidationError as e:
        log_utils.logger.error(
            f"Failed to validate raw data to model '{scheme_type.__name__}': {e}"
        )
        return None

    return data

def _filter_data(model) -> dict[str, Decimal]|None:
    rv = {}
    if isinstance(model, DataScheme_CBRXMLDaily):
        for item in model.Valute.values():
            if currency.get_currency_type(item.CharCode) is None:
                continue

            rv[item.CharCode] = Decimal(item.Value)

        return rv

    log_utils.logger.error(
        "Filer function failed, unknown model type: '{}', model: {}".format(
            type(model).__name__,
            model
        )
    )
    return None

async def start_currency_fetcher(
    url: str,
    scheme_type: type[V],
    period: int,
    timeout: int = 30
):
    """
    Continuously fetches currency data and updates app state
    """
    async for raw_data in _fetch(url, period, timeout=timeout):
        raw_model = _validate(raw_data, scheme_type)
        data = _filter_data(raw_model)
        if data:
            await app.app_state.set_exchange_rates(**data)
            if not app.is_debug_mode():
                log_utils.logger.info("Exchange rates were updated")
