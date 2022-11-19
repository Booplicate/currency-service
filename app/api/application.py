"""
Modules implements base API backend
"""

from typing import Callable

import fastapi

from . import endpoints


app = fastapi.FastAPI()

app.include_router(endpoints.router)
