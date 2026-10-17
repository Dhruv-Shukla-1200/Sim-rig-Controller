#!/usr/bin/env python3
"""Entry point for the Sim Rig Controller server.

Usage:
  python server/main.py                 # dashboard + phone (USB auto-setup and Wi-Fi)
  python server/main.py --no-vjoy       # dashboard only, no vJoy output
  python server/main.py --code 1234     # fixed Wi-Fi pairing code
  python server/main.py --no-adb        # do not run adb (Wi-Fi only / manual USB)
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

from server.common.config import DEFAULT_WS_PORT, HOST
from server.websocket.ws_server import run_ws_server


def main():
    parser = argparse.ArgumentParser(
        description="Sim-rig-Controller server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["ws", "websocket"],
        default="ws",
        help="Kept so `--mode ws` still works. WebSocket is the only mode.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_WS_PORT, help="Port to bind")
    parser.add_argument("--host", default=HOST, help="Host address to bind")
    parser.add_argument("--code", help="Fixed 4-digit pairing code (Wi-Fi mode)")
    parser.add_argument(
        "--no-vjoy",
        action="store_true",
        help="Disable vJoy output (dashboard / testing only)",
    )
    parser.add_argument(
        "--no-adb",
        action="store_true",
        help="Do not run adb automatically (USB tunnel must then be set up by hand)",
    )
    parser.add_argument(
        "--no-auto-launch",
        action="store_true",
        help="Do not open the SimWheel app on the phone automatically",
    )
    args = parser.parse_args()

    run_ws_server(
        host=args.host,
        port=args.port,
        code=args.code,
        no_vjoy=args.no_vjoy,
        auto_adb=not args.no_adb,
        auto_launch=not args.no_auto_launch,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[server] Stopped.")
