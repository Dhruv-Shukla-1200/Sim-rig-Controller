"""Shared configuration and constants for Sim-rig-Controller."""
import os
import shutil

# --- Networking ---
HOST = "0.0.0.0"
DEFAULT_WS_PORT = 8080
DEFAULT_TCP_PORT = 5555

# Backward compatibility aliases
PORT = DEFAULT_TCP_PORT
TCP_PORT = DEFAULT_TCP_PORT

# --- vJoy Device ---
VJOY_DEVICE_ID = 1

# vJoy axes go from 0 to 0x8000 (32768)
AXIS_MIN = 0x0000
AXIS_MAX = 0x8000
AXIS_CENTER = 0x4000

# Button indices (1-based for vJoy)
BUTTON_GEAR_UP = 1
BUTTON_GEAR_DOWN = 2
BUTTON_HANDBRAKE = 3

# --- Android / ADB ---
ANDROID_PACKAGE = "com.example.simwheel"
ANDROID_ACTIVITY = ".MainActivity"


def resolve_adb_path() -> str:
    """Find adb on system PATH or in typical Android SDK locations."""
    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb

    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\platform-tools\adb.exe"),
        r"C:\Users\DHRUV\AppData\Local\platform-tools\adb.exe",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return "adb"


ADB_PATH = resolve_adb_path()
