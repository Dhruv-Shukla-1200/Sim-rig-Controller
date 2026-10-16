"""Entry point for Wired (USB ADB + TCP) server."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.config import DEFAULT_TCP_PORT
from server.common.vjoy_output import init_vjoy, apply_packet, reset_all
from server.wired.tcp_server import start_server, wait_for_connection, receive_packets
from server.wired.adb_utils import check_adb_available, check_device_connected, reverse_port, launch_app


def run_wired_server(port: int = DEFAULT_TCP_PORT, auto_launch: bool = True):
    print("=" * 52)
    print("  SIM RIG CONTROLLER - WIRED (USB) MODE")
    print(f"  Target Port: {port}")
    print("=" * 52)

    adb_ok = check_adb_available()
    if adb_ok:
        device_ok = check_device_connected()
        if device_ok:
            reverse_port(port)
            if auto_launch:
                launch_app()
    else:
        print("[wired] Warning: Proceeding without automatic ADB configuration.")

    device = init_vjoy()
    server = start_server(port=port)

    try:
        while True:
            conn, addr = wait_for_connection(server)
            try:
                for packet in receive_packets(conn):
                    apply_packet(device, packet)
            finally:
                reset_all(device)
                conn.close()
                print("[wired] Client disconnected. Waiting for next connection...")
    except KeyboardInterrupt:
        print("\n[wired] Shutting down...")
    finally:
        reset_all(device)
        server.close()


if __name__ == "__main__":
    run_wired_server()
