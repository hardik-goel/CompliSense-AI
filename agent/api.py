from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan

app = FastAPI(title="EUAI Local Agent")

class ScanReq(BaseModel):
    root: str
    pack_path: str


@app.get("/")
def read_root():
    return {"status": "EU AI Act agent is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/scan")
async def scan_endpoint(root: str, pack: str):
    results = run_scan(Path(root), iter_rules(load_rulepack(Path(pack))))
    return results