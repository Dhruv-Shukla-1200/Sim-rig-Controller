# main.py — entry point: wires together adb setup, the TCP server, and vJoy output.
# Running `python main.py` alone now replaces:
#   1. adb devices
#   2. adb reverse tcp:5555 tcp:5555
#   3. opening the app on the phone (attempted automatically; manual fallback if it fails)
#   4. starting the server + vJoy

from vjoy_output import init_vjoy, apply_packet, reset_all
from tcp_server import start_server, wait_for_connection, receive_packets
from adb_utils import check_adb_available, check_device_connected, reverse_port, launch_app


def main():
    if not check_adb_available():
        return
    if not check_device_connected():
        return
    if not reverse_port():
        return

    launch_app()  # non-fatal if this fails — open the app on the phone manually if needed

    device = init_vjoy()
    server = start_server()

    try:
        while True:  # keep accepting new connections after disconnects
            conn, addr = wait_for_connection(server)
            try:
                for packet in receive_packets(conn):
                    apply_packet(device, packet)
            finally:
                reset_all(device)  # zero out on disconnect, before waiting for next client
                conn.close()
                print("Waiting for next connection...")
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        reset_all(device)


if __name__ == "__main__":
    main()