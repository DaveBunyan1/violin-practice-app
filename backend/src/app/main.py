from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.lifespan import lifespan

from app.api.v1.repertoire import router as repertoire_router
from app.api.v1.session import router as session_router
from app.api.v1.live_stream import router as live_stream_router

# -----------------------------------------------------------------
#  FastAPI Initialization
# -----------------------------------------------------------------
app = FastAPI(
    title="Violin Intonation Pipeline API",
    version="1.3.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(repertoire_router, prefix="/repertoire", tags=["repertoire"])
app.include_router(session_router, prefix="/session", tags=["session"])
app.include_router(live_stream_router, tags=["live_stream"])
