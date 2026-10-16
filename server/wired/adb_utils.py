"""ADB utilities for wired USB connection and automation."""
import subprocess
import sys
from pathlib import Path

# Add project root to path if running directly
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.config import ADB_PATH, TCP_PORT, ANDROID_PACKAGE, ANDROID_ACTIVITY


def check_adb_available() -> bool:
    """Confirms adb is installed and reachable."""
    try:
        subprocess.run([ADB_PATH, "version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"[adb] adb not found at '{ADB_PATH}'. Check that it's installed and on PATH.")
        return False


def check_device_connected() -> bool:
    """Confirms an Android device is attached via USB."""
    try:
        result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
        lines = [line for line in result.stdout.strip().splitlines()[1:] if line.strip()]
        if not lines:
            print("[adb] No device found. Is USB debugging enabled and the phone connected?")
            return False
        print(f"[adb] Device connected: {lines[0]}")
        return True
    except Exception as exc:
        print(f"[adb] Error checking devices: {exc}")
        return False


def reverse_port(port: int = TCP_PORT) -> bool:
    """Run `adb reverse tcp:<port> tcp:<port>` to tunnel traffic over USB."""
    try:
        result = subprocess.run(
            [ADB_PATH, "reverse", f"tcp:{port}", f"tcp:{port}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[adb] adb reverse failed: {result.stderr.strip()}")
            return False
        print(f"[adb] Port {port} reversed (phone -> PC over USB).")
        return True
    except Exception as exc:
        print(f"[adb] Error executing adb reverse: {exc}")
        return False


def launch_app() -> bool:
    """Launches the sim wheel app on the phone automatically."""
    try:
        result = subprocess.run(
            [ADB_PATH, "shell", "am", "start", "-n", f"{ANDROID_PACKAGE}/{ANDROID_ACTIVITY}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[adb] Could not launch app automatically: {result.stderr.strip()}")
            print("[adb] Please open the app on your phone manually.")
            return False
        print("[adb] App launched on phone.")
        return True
    except Exception as exc:
        print(f"[adb] Error launching app: {exc}")
        return False
