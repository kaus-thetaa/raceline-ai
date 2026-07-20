# api/server.py
# local fastapi server exposing live stats and graph over http

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

STATS_FILE_PATH = "data/live_stats.json"
DATA_DIR = "data"

app = FastAPI(title="raceline-ai stats api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


@app.get("/api/stats")
def get_stats():
    if not os.path.exists(STATS_FILE_PATH):
        raise HTTPException(status_code=404, detail="stats file not found yet")

    with open(STATS_FILE_PATH, "r") as f:
        data = json.load(f)

    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)