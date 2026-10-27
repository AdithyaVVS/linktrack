from fastapi import FastAPI

app = FastAPI(title="LinkTrack")

@app.get("/api/health")
def health():
    return {"status": "ok"}