# tcp_server.py — TCP server that receives newline-delimited JSON packets.
# Run this file directly to test the server alone (prints received packets).

import socket
import json
from config import HOST, PORT


def start_server():
    """Create and bind the server socket. Call once at startup."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    server.settimeout(1.0)
    print(f"Listening on {HOST}:{PORT}...")
    return server


def wait_for_connection(server):
    while True:
        try:
            conn, addr = server.accept()
            print(f"Connected: {addr}")
            return conn, addr
        except socket.timeout:
            continue  # loop back, gives Ctrl+C a chance to interrupt


def receive_packets(conn):
    """Generator: yields parsed JSON dicts, one per line, as they arrive.
    Skips malformed lines instead of crashing. Stops when connection closes
    or drops.
    """
    reader = conn.makefile("r")
    try:
        for line in reader:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping malformed packet: {line!r}")
                continue
            yield data
    except (ConnectionResetError, BrokenPipeError):
        print("Connection lost.")
    finally:
        reader.close()


# --- Standalone test ---
if __name__ == "__main__":
    server = start_server()

    while True:  # outer loop: accept a new connection after each disconnect
        conn, addr = wait_for_connection(server)
        for packet in receive_packets(conn):
            print("Received:", packet)
        conn.close()
        print("Waiting for next connection...")