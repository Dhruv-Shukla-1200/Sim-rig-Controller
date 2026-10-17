"""ADB helpers: make the USB connection work without typing adb commands.

The phone app in USB mode connects to ws://127.0.0.1:8080. `adb reverse`
makes that address on the phone point at this laptop through the USB cable.
"""
import subprocess
from typing import Optional

from server.common.config import ADB_PATH, ANDROID_ACTIVITY, ANDROID_PACKAGE


def _run(args, timeout=15):
    return subprocess.run(
        [ADB_PATH, *args], capture_output=True, text=True, timeout=timeout
    )


def adb_available() -> bool:
    """True if the adb executable can be run."""
    try:
        _run(["version"])
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def device_state() -> Optional[str]:
    """State of the first attached phone: 'device', 'unauthorized', 'offline',
    or None when nothing is attached (or adb cannot be queried)."""
    try:
        out = _run(["devices"]).stdout.strip().splitlines()[1:]
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out:
        parts = line.split()
        if len(parts) >= 2:
            return parts[1]
    return None


def tunnel_active(port: int) -> bool:
    """True if `adb reverse` already forwards tcp:<port> to this laptop."""
    try:
        return f"tcp:{port}" in _run(["reverse", "--list"]).stdout
    except (OSError, subprocess.SubprocessError):
        return False


def reverse_port(port: int) -> Optional[str]:
    """Set up the USB tunnel. Returns None on success, else the error text."""
    try:
        result = _run(["reverse", f"tcp:{port}", f"tcp:{port}"])
    except (OSError, subprocess.SubprocessError) as exc:
        return str(exc)
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip() or "adb reverse failed"
    return None


def launch_app() -> bool:
    """Open the SimWheel app on the phone."""
    try:
        result = _run(["shell", "am", "start", "-n",
                       f"{ANDROID_PACKAGE}/{ANDROID_ACTIVITY}"])
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
