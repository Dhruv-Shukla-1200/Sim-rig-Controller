# adb_utils.py — wraps the adb commands needed to connect to the phone,
# so main.py can set up the connection automatically instead of requiring
# manual terminal commands before every session.

import subprocess
from config import ADB_PATH, TCP_PORT, ANDROID_PACKAGE, ANDROID_ACTIVITY


def check_adb_available():
    """Confirms adb itself is installed and reachable."""
    try:
        subprocess.run([ADB_PATH, "version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"adb not found at '{ADB_PATH}'. Check it's installed and on PATH.")
        return False


def check_device_connected():
    """Equivalent of: adb devices — confirms a device is attached.
    Returns True if at least one device is listed as connected.
    """
    result = subprocess.run(
        [ADB_PATH, "devices"], capture_output=True, text=True
    )
    lines = [l for l in result.stdout.strip().splitlines()[1:] if l.strip()]
    if not lines:
        print("No device found. Is USB debugging enabled and the phone plugged in?")
        return False
    print(f"Device connected: {lines[0]}")
    return True


def reverse_port():
    """Equivalent of: adb reverse tcp:5555 tcp:5555
    Lets the phone (acting as TCP client) reach the laptop's server
    at localhost:5555, tunneled over USB.
    """
    result = subprocess.run(
        [ADB_PATH, "reverse", f"tcp:{TCP_PORT}", f"tcp:{TCP_PORT}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"adb reverse failed: {result.stderr.strip()}")
        return False
    print(f"Port {TCP_PORT} reversed (phone -> laptop).")
    return True


def launch_app():
    """Launches the sim wheel app on the phone automatically.
    Non-fatal if it fails — you can always open the app by hand instead.
    """
    result = subprocess.run(
        [ADB_PATH, "shell", "am", "start", "-n", f"{ANDROID_PACKAGE}/{ANDROID_ACTIVITY}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Could not launch app automatically: {result.stderr.strip()}")
        print("Open the app on your phone manually.")
        return False
    print("App launched on phone.")
    return True