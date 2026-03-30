"""
DramaForge - AI Short Drama Engine
Run this file to start the server.

Usage:
    python main.py
    # or
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn

from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
