import threading
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentConfig:
    upload_enabled: bool = False
    saas_url: Optional[str] = None
    token: Optional[str] = None
    llm_enabled: bool = False
    tier: str = "FREE"   # FREE | PRO | ULTRA
    cancel_flag: threading.Event = threading.Event()

