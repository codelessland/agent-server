import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import Config
from .routers import conversation_router, event_router, sockets

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    app.state.config = config
    app.state.event_services: dict[UUID, "EventService"] = {}
    logger.info("Agent server started on %s:%s", config.host, config.port)
    yield
    for svc in app.state.event_services.values():
        await svc.close()
    logger.info("Agent server stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Server", version="0.1.0", lifespan=lifespan)
    app.include_router(conversation_router.router)
    app.include_router(event_router.router)
    app.include_router(sockets.router)

    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():
        return RedirectResponse(url="/static/index.html")

    return app


app = create_app()
