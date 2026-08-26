"""Run the demo server with ``python -m data_agent_network_demo``."""

from __future__ import annotations

import argparse
import threading
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Data Agent Network demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--open", action="store_true", help="Open the demo in the default browser.")
    args = parser.parse_args()

    if args.open:
        threading.Timer(0.8, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    uvicorn.run("data_agent_network_demo.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
