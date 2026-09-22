"""Application launcher for xBookLibrary.

Starts the FastAPI server with production React frontend mounted,
and automatically opens the default web browser.
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")


def main():
    print("=" * 60)
    print("  Starting xBookLibrary v1.2.9.22...")
    print("  Calibre-Compatible AI Book Library Platform")
    print("  Web Interface: http://127.0.0.1:8000")
    print("  OPDS Feed:     http://127.0.0.1:8000/opds")
    print("=" * 60)

    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Uvicorn web server
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
