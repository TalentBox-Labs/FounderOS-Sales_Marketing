from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from revenue_os.api.v1 import v1_router
from revenue_os.database import engine, get_db
from revenue_os.integrations.webhooks import router as webhooks_router
from revenue_os.models.base import Base
from revenue_os.services.revenue_intelligence import get_dashboard_stats

app = FastAPI(
    title="Revenue OS",
    version="0.1.0",
    description="AI-first Revenue Operating System for WorkCrew & HireStack",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
app.include_router(webhooks_router)

static_dir = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@app.get("/")
def serve_frontend():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Revenue OS API — frontend not built"}
