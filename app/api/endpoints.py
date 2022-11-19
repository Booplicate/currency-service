"""
Modules defines API endpoints

The paths are required by the specification, no questions
"""

import fastapi
from fastapi import (
    responses,
    status
)

import app
from .. import (
    currency,
    log_utils
)
from . import models


router = fastapi.APIRouter(
    dependencies=[fastapi.Depends(log_utils.log_request_content)]
)


@router.get("/amount/get", response_model=None, response_class=responses.PlainTextResponse)
async def get_amount():
    return await app.app_state.generate_report()

@router.get("/{id}/get")
async def get_currency(id: str):
    currency_name = id.upper()
    try:
        value = await app.app_state.get_balance(currency_name)

    except currency.CurrencyError as e:
        # log_utils.logger.info(f"Request expectedly failed: {e}")
        raise fastapi.HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Failed to process currency '{id}': {e}"
        )

    return {"name": currency_name, "value": value}

@router.post("/amount/set", status_code=status.HTTP_204_NO_CONTENT)
async def post_amount(data: models.CurrencyChangeModel):# type: ignore
    try:
        for k, v in data.dict().items():# type: ignore
            if v is None:
                continue

            k = k.upper()
            await app.app_state.set_balance(k, v)

    except currency.CurrencyError as e:
        # log_utils.logger.info(f"Request expectedly failed: {e}")
        raise fastapi.HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process payload: {e}"
        )

    return

@router.post("/modify", status_code=status.HTTP_204_NO_CONTENT)
async def post_modify(data: models.CurrencyChangeModel):# type: ignore
    try:
        for k, v in data.dict().items():# type: ignore
            if v is None:
                continue

            k = k.upper()

            if v < currency.MIN_AMOUNT:
                await app.app_state.remove_balance(k, abs(v))

            else:
                await app.app_state.add_balance(k, v)

    except currency.CurrencyError as e:
        # log_utils.logger.info(f"Request expectedly failed: {e}")
        raise fastapi.HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process payload: {e}"
        )

    return
