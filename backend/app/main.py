from fastapi import FastAPI

from app.routes import links

app = FastAPI(title="LinkTrack")

app.include_router(links.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
