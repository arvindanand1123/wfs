"""FastAPI application entrypoint.

Run locally:  uvicorn wfs.main:app --reload
In container:  uvicorn wfs.main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI

from wfs import __version__
from wfs.controllers import objects


def create_app():
    """App factory. Keeps wiring in one place and makes testing easy."""
    app = FastAPI(title="wfs", version=__version__)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "version": __version__}

    app.include_router(objects.router)
    return app


app = create_app()
