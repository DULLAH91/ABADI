from __future__ import annotations
import os
import uvicorn
from .server import create_app
def main() -> None:
    uvicorn.run(create_app(),host=os.getenv("AI_MEDIA_HUB_AGENT_HOST","127.0.0.1"),port=int(os.getenv("AI_MEDIA_HUB_AGENT_PORT","8787")))
