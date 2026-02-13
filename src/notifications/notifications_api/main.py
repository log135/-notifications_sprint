from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from notifications.common.health_files import is_ready, mark_ready, clear_ready
from notifications.notifications_api.api.v1 import events, templates
from notifications.notifications_api.utils.dependencies import get_kafka_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    clear_ready()
    publisher = get_kafka_publisher()
    await publisher.start()
    mark_ready()
    yield
    clear_ready()
    await publisher.stop()


app = FastAPI(
    title="Notifications API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    if is_ready():
        return Response(status_code=200)
    return Response(status_code=503)


app.include_router(events.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
