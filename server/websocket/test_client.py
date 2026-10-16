#!/usr/bin/env python3
"""Fake phone client for testing the WebSocket server without the Android app.

Usage:
    python test_client.py                                    # Local USB-style
    python test_client.py --host 192.168.1.5 --code 4821     # Wi-Fi style
"""
import argparse
import asyncio
import json
import math
import time
import aiohttp


async def run(host, port, code):
    url = f"ws://{host}:{port}/ws/phone" + (f"?code={code}" if code else "")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print(f"[test_client] Connected to {url}")

            async def listen():
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue
                    data = json.loads(msg.data)
                    if data.get("type") == "ping":
                        await ws.send_json({"type": "pong", "ts": data["ts"]})
                    elif data.get("type") == "latency":
                        print(f"[test_client] Latency: {data['rtt']} ms (jitter: {data['jitter']} ms)")

            task = asyncio.create_task(listen())
            t0 = time.time()
            try:
                while True:
                    t = time.time() - t0
                    await ws.send_json({
                        "steering": round(math.sin(t * 0.8), 3),
                        "throttle": round(max(0.0, math.sin(t * 0.4)), 3),
                        "brake": round(max(0.0, -math.sin(t * 0.4)), 3),
                        "gear_up": int(t * 2) % 10 == 0 and (t * 2) % 1 < 0.15,
                        "gear_down": False,
                    })
                    await asyncio.sleep(1 / 60)
            finally:
                task.cancel()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--code")
    args = ap.parse_args()
    try:
        asyncio.run(run(args.host, args.port, args.code))
    except KeyboardInterrupt:
        pass
