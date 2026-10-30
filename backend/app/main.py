from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routes import links, redirect

app = FastAPI(title="LinkTrack")

app.include_router(links.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/app/index.html")


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Must be last: this is a catch-all route
app.include_router(redirect.router)
