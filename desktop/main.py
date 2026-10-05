# main.py — entry point: wires together the TCP server and vJoy output.

from vjoy_output import init_vjoy, apply_packet, reset_all
from tcp_server import start_server, wait_for_connection, receive_packets


def main():
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