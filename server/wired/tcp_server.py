"""TCP server for low-latency wired USB communication."""
import json
import socket
import sys
from pathlib import Path
from typing import Generator, Tuple, Dict, Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.config import HOST, DEFAULT_TCP_PORT


def start_server(host: str = HOST, port: int = DEFAULT_TCP_PORT) -> socket.socket:
    """Create and bind the TCP server socket."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    server.settimeout(1.0)  # non-blocking timeout allows Ctrl+C interrupt
    print(f"[wired] Listening on {host}:{port}...")
    return server


def wait_for_connection(server: socket.socket) -> Tuple[socket.socket, Any]:
    """Wait until a client connects, retrying on timeout."""
    while True:
        try:
            conn, addr = server.accept()
            print(f"[wired] Client connected: {addr}")
            return conn, addr
        except socket.timeout:
            continue


def receive_packets(conn: socket.socket) -> Generator[Dict[str, Any], None, None]:
    """Generator: yields parsed JSON packets line-by-line."""
    reader = conn.makefile("r", encoding="utf-8")
    try:
        for line in reader:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[wired] Skipping malformed packet: {line!r}")
                continue
            yield data
    except (ConnectionResetError, BrokenPipeError):
        print("[wired] Connection lost.")
    finally:
        reader.close()


if __name__ == "__main__":
    srv = start_server()
    try:
        while True:
            c, a = wait_for_connection(srv)
            for pkt in receive_packets(c):
                print("[wired] Received:", pkt)
            c.close()
            print("[wired] Waiting for next connection...")
    except KeyboardInterrupt:
        print("\n[wired] Shutting down...")
    finally:
        srv.close()
