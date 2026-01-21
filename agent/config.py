import threading
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentConfig:
    upload_enabled: bool = False
    saas_url: Optional[str] = None
    token: Optional[str] = None
    llm_enabled: bool = False
    cancel_flag: threading.Event = threading.Event()
    PASS_THRESHOLD = 0.55
    WARN_THRESHOLD = 0.40
