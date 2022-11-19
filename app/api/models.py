
from decimal import Decimal
import pydantic


from .. import currency


# Describes a model for a payload to change balance
# This has to be defined dynamically
# pylint: disable=no-member
CurrencyChangeModel = pydantic.create_model(# type: ignore
    "CurrencyChangeModel",
    **{
        name.lower(): (Decimal, None)
        for name in currency.get_currency_types().keys()
    }
)
