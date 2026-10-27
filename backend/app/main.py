from fastapi import FastAPI

from app.routes import links, redirect

app = FastAPI(title="LinkTrack")

app.include_router(links.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Must be last: this is a catch-all route
app.include_router(redirect.router)
