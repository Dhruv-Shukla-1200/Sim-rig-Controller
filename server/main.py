#!/usr/bin/env python3
"""Unified entry point for Sim Rig Controller Server.

Usage:
  python main.py --mode ws     # Run WebSocket server (dashboard + Wi-Fi / USB WS)
  python main.py --mode wired  # Run low-latency direct TCP server over USB ADB
"""
import argparse
import asyncio
import sys
from pathlib import Path

# On Windows, aiohttp requires SelectorEventLoop; must be set BEFORE any import
# of aiohttp to avoid garbled tracebacks and 'Unhandled exception' on Ctrl+C.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.config import DEFAULT_WS_PORT, DEFAULT_TCP_PORT, HOST
from server.wired.main_wired import run_wired_server
from server.websocket.ws_server import run_ws_server


def main():
    parser = argparse.ArgumentParser(
        description="Sim-rig-Controller Server (Unified Runner)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["ws", "websocket", "wired", "tcp"],
        default="ws",
        help="Server connection mode: 'ws' (WebSocket & Web Dashboard) or 'wired' (Direct TCP over USB ADB)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind (defaults to 8080 for ws, 5555 for wired)",
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help="Host address to bind",
    )
    parser.add_argument(
        "--code",
        help="Fixed 4-digit pairing code (WebSocket mode only)",
    )
    parser.add_argument(
        "--no-vjoy",
        action="store_true",
        help="Disable vJoy hardware output (dashboard / testing only)",
    )
    parser.add_argument(
        "--no-auto-launch",
        action="store_true",
        help="Disable auto-launching Android app via ADB in wired mode",
    )

    args = parser.parse_args()

    mode = args.mode.lower()
    if mode in ("wired", "tcp"):
        port = args.port or DEFAULT_TCP_PORT
        run_wired_server(port=port, auto_launch=not args.no_auto_launch)
    else:
        port = args.port or DEFAULT_WS_PORT
        run_ws_server(
            host=args.host,
            port=port,
            code=args.code,
            no_vjoy=args.no_vjoy,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[server] Stopped.")
