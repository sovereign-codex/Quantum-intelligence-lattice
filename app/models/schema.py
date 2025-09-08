from pydantic import BaseModel
from typing import Optional, List, Dict

class VOT(BaseModel):
    day: int
    date: str
    theme: str
    name: str
    deliverable: str
    metrics_template: str
    status: str = "Open"
    deps: List[int] = []

class Run(BaseModel):
    id: int
    day: int
    ok: bool
    started_at: str
    finished_at: str
    artifacts: Dict[str, str] = {}
