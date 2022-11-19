"""
Modules implements RESTful API for accessing the service
"""

import uvicorn

from . import (
    application,
    endpoints,
    models
)
from .application import (
    app,
    add_quit_callback
)

from .. import log_utils

# APP_PATH = "app.api.application:app"


def build_uvicorn_server(host="0.0.0.0", port=8080) -> uvicorn.Server:
    """
    Builds an ASGI server
    """
    cfg = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=log_utils.get_lib_log_level()
    )
    return uvicorn.Server(cfg)


async def start_server(server=None):
    """
    Launches API server in the current async loop
    NOTE: by default uses uvicorn
    """
    if server is None:
        server = build_uvicorn_server()
    await server.serve()
