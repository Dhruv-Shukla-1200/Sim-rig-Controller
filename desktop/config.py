# config.py — shared constants for the desktop app

# --- Networking ---
HOST = "0.0.0.0"
PORT = 5555

# --- vJoy device ---
VJOY_DEVICE_ID = 1

# --- Axis value ranges ---
# vJoy axes go from 0 to 0x8000 (32768)
AXIS_MIN = 0x0000
AXIS_MAX = 0x8000
AXIS_CENTER = 0x4000

# --- Button numbers (as configured in vJoy Config panel) ---
BUTTON_GEAR_UP = 1
BUTTON_GEAR_DOWN = 2
BUTTON_HANDBRAKE = 3

# --- ADB / Android ---
ADB_PATH = r"C:\Users\DHRUV\AppData\Local\platform-tools\adb.exe"
TCP_PORT = PORT            # reuse the existing PORT value for adb reverse
ANDROID_PACKAGE = "com.example.simwheel"
ANDROID_ACTIVITY = ".MainActivity"