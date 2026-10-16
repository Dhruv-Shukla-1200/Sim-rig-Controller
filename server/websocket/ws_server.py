#!/usr/bin/env python3
"""Sim Wheel WebSocket Server.

Serves:
  GET  /               web dashboard (live inputs, status, latency, mini-game)
  WS   /ws/phone       phone client stream
  WS   /ws/dashboard   dashboard telemetry stream
"""
import argparse
import asyncio
import json
import logging
import random
import socket
import sys
import time
from collections import deque
from pathlib import Path

# On Windows, aiohttp requires SelectorEventLoop; ProactorEventLoop causes
# garbled tracebacks and 'Unhandled exception' noise on Ctrl+C.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Suppress spurious 'Task exception was never retrieved' logs from aiohttp
logging.getLogger("aiohttp").setLevel(logging.WARNING)

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiohttp import WSMsgType, web
from server.common.config import DEFAULT_WS_PORT, HOST
from server.common.vjoy_output import VJoyOutput

LOOPBACK = {"127.0.0.1", "::1"}
ZERO = {
    "steering": 0.0,
    "throttle": 0.0,
    "brake": 0.0,
    "gear_up": False,
    "gear_down": False,
    "handbrake": False,
}


def now_ms() -> float:
    return time.perf_counter() * 1000.0


def lan_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def num(data, key, lo, hi):
    v = data.get(key, 0)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return 0.0
    return max(lo, min(hi, float(v)))


def clean_packet(data):
    return {
        "steering": num(data, "steering", -1.0, 1.0),
        "throttle": num(data, "throttle", 0.0, 1.0),
        "brake": num(data, "brake", 0.0, 1.0),
        "gear_up": data.get("gear_up") is True,
        "gear_down": data.get("gear_down") is True,
        "handbrake": data.get("handbrake") is True,
    }


class Hub:
    def __init__(self, code: str, output: VJoyOutput, port: int):
        self.code = code
        self.output = output
        self.port = port
        self.phone = None
        self.dashboards = set()
        self.mode = None
        self.hz = 0
        self.packets = 0
        self.rtts = deque(maxlen=30)

    def jitter(self):
        r = list(self.rtts)
        if len(r) < 2:
            return 0.0
        return sum(abs(a - b) for a, b in zip(r, r[1:])) / (len(r) - 1)

    def hello(self):
        ips = lan_ips()
        return {
            "type": "hello",
            "code": self.code,
            "port": self.port,
            "ips": ips,
            "addresses": ips,
            "vjoy": self.output.available,
            "phone": self.phone is not None,
            "mode": self.mode,
            "hz": self.hz,
            "status": self.status(),
        }

    def status(self):
        return {
            "type": "status",
            "connected": self.phone is not None,
            "mode": self.mode,
            "hz": self.hz,
            "latency": round(self.rtts[-1], 1) if self.rtts else None,
            "jitter": round(self.jitter(), 1) if self.rtts else None,
            "vjoy": self.output.available,
        }

    async def broadcast(self, msg: dict):
        if not self.dashboards:
            return
        payload = json.dumps(msg)
        dead = []
        for ws in self.dashboards:
            try:
                await ws.send_str(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.dashboards.discard(ws)

    async def send_to_phone(self, msg: dict):
        if self.phone is not None and not self.phone.closed:
            try:
                await self.phone.send_str(json.dumps(msg))
            except Exception:
                pass


async def index(request):
    html_path = ROOT / "game" / "dashboard.html"
    if not html_path.exists():
        html_path = Path(__file__).resolve().parent / "dashboard.html"
    return web.FileResponse(html_path)


async def phone_ws(request):
    hub = request.app["hub"]
    is_local = request.remote in LOOPBACK
    if not is_local and request.query.get("code") != hub.code:
        return web.Response(status=403, text="wrong code")

    ws = web.WebSocketResponse(heartbeat=5, max_msg_size=4096)
    await ws.prepare(request)

    if hub.phone is not None and not hub.phone.closed:
        await hub.phone.close(code=4000, message=b"replaced by a new phone")
    hub.phone, hub.mode = ws, ("usb" if is_local else "wifi")
    hub.rtts.clear()
    hub.packets = 0
    print(f"[ws:phone] Connected via {hub.mode} from {request.remote}")
    await hub.broadcast(hub.status())

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            kind = data.get("type", "input")

            if kind == "pong":
                ts = data.get("ts")
                if isinstance(ts, (int, float)) and not isinstance(ts, bool):
                    rtt = now_ms() - ts
                    if 0 <= rtt < 10000:
                        hub.rtts.append(rtt)
                        lat = {
                            "type": "latency",
                            "rtt": round(rtt, 1),
                            "jitter": round(hub.jitter(), 1),
                        }
                        await hub.broadcast(lat)
                        await ws.send_str(json.dumps(lat))
            elif kind == "input":
                pkt = clean_packet(data)
                hub.packets += 1
                hub.output.apply_packet(pkt)
                await hub.broadcast({"type": "input", **pkt})
    finally:
        if hub.phone is ws:
            hub.phone, hub.mode, hub.hz = None, None, 0
            hub.output.reset_all()
            print("[ws:phone] Disconnected, outputs reset")
            await hub.broadcast(hub.status())
            await hub.broadcast({"type": "input", **ZERO})
    return ws


async def dashboard_ws(request):
    hub = request.app["hub"]
    ws = web.WebSocketResponse(heartbeat=10)
    await ws.prepare(request)
    hub.dashboards.add(ws)
    await ws.send_str(json.dumps(hub.hello()))
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if isinstance(data, dict) and data.get("type") == "vibrate":
                        duration = int(data.get("duration", 200))
                        await hub.send_to_phone({"type": "vibrate", "duration": duration})
                except Exception:
                    pass
    finally:
        hub.dashboards.discard(ws)
    return ws


async def ping_loop(hub):
    while True:
        await asyncio.sleep(1)
        ws = hub.phone
        if ws is not None and not ws.closed:
            try:
                await ws.send_str(json.dumps({"type": "ping", "ts": now_ms()}))
            except Exception:
                pass


async def status_loop(hub):
    while True:
        await asyncio.sleep(1)
        hub.hz, hub.packets = hub.packets, 0
        await hub.broadcast(hub.status())


async def background(app):
    hub = app["hub"]
    tasks = [
        asyncio.create_task(ping_loop(hub)),
        asyncio.create_task(status_loop(hub)),
    ]
    yield
    for t in tasks:
        t.cancel()
    hub.output.reset_all()


def run_ws_server(
    host: str = HOST,
    port: int = DEFAULT_WS_PORT,
    code: str = None,
    no_vjoy: bool = False,
):
    pair_code = code or f"{random.randint(0, 9999):04d}"
    hub = Hub(pair_code, VJoyOutput(enabled=not no_vjoy), port)

    app = web.Application()
    app["hub"] = hub
    app.router.add_get("/", index)
    app.router.add_get("/ws/phone", phone_ws)
    app.router.add_get("/ws/dashboard", dashboard_ws)
    app.cleanup_ctx.append(background)

    print("=" * 52)
    print("  SIM RIG CONTROLLER - WEBSOCKET SERVER")
    print(f"  Dashboard : http://localhost:{port}")
    print(f"  Pair code : {pair_code}   (Wi-Fi mode only)")
    for ip in lan_ips():
        print(f"  Wi-Fi addr: {ip}:{port}")
    print(f"  USB mode  : adb reverse tcp:{port} tcp:{port}")
    print(f"  vJoy      : {'on' if hub.output.available else 'off'}")
    print("=" * 52)
    try:
        web.run_app(app, host=host, port=port, print=None)
    except KeyboardInterrupt:
        print("\n[server] Stopped.")
    finally:
        hub.output.reset_all()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sim Wheel WebSocket server")
    ap.add_argument("--port", type=int, default=DEFAULT_WS_PORT)
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--code", help="fixed 4-digit pairing code (default: random)")
    ap.add_argument("--no-vjoy", action="store_true", help="run without vJoy")
    args = ap.parse_args()
    run_ws_server(args.host, args.port, args.code, args.no_vjoy)
