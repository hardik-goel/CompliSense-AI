from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan

app = FastAPI(title="EUAI Local Agent")

class ScanReq(BaseModel):
    root: str
    pack_path: str

@app.post("/scan")
def scan(req: ScanReq):
    rp = load_rulepack(Path(req.pack_path))
    return run_scan(Path(req.root), iter_rules(rp))
