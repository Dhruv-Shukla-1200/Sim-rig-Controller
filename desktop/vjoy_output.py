# vjoy_output.py — wraps all pyvjoy calls behind simple functions.
# Run this file directly to test vJoy output without any networking.

import pyvjoy
from mapping import normalize
from config import (
    VJOY_DEVICE_ID,
    AXIS_MIN, AXIS_MAX, AXIS_CENTER,
    BUTTON_GEAR_UP, BUTTON_GEAR_DOWN, BUTTON_HANDBRAKE,
)


def init_vjoy():
    """Connect to the vJoy device. Call this once at startup."""
    return pyvjoy.VJoyDevice(VJOY_DEVICE_ID)


def set_steering(device, value):
    """value: float, -1.0 (full left) to 1.0 (full right)."""
    device.set_axis(pyvjoy.HID_USAGE_X, normalize(value, -1.0, 1.0, AXIS_MIN, AXIS_MAX))


def set_throttle(device, value):
    """value: float, 0.0 to 1.0."""
    device.set_axis(pyvjoy.HID_USAGE_Y, normalize(value, 0.0, 1.0, AXIS_MIN, AXIS_MAX))


def set_brake(device, value):
    """value: float, 0.0 to 1.0."""
    device.set_axis(pyvjoy.HID_USAGE_Z, normalize(value, 0.0, 1.0, AXIS_MIN, AXIS_MAX))


def set_gear_up(device, pressed: bool):
    device.set_button(BUTTON_GEAR_UP, 1 if pressed else 0)


def set_gear_down(device, pressed: bool):
    device.set_button(BUTTON_GEAR_DOWN, 1 if pressed else 0)


def set_handbrake(device, pressed: bool):
    device.set_button(BUTTON_HANDBRAKE, 1 if pressed else 0)


def apply_packet(device, data: dict):
    """Apply a parsed JSON packet (dict) to the vJoy device.
    Uses .get() with defaults so missing/optional fields don't crash this.
    """
    set_steering(device, data.get("steering", 0.0))
    set_throttle(device, data.get("throttle", 0.0))
    set_brake(device, data.get("brake", 0.0))
    set_gear_up(device, data.get("gear_up", False))
    set_gear_down(device, data.get("gear_down", False))
    set_handbrake(device, data.get("handbrake", False))


def reset_all(device):
    """Zero out all axes/buttons — call on disconnect or shutdown."""
    device.set_axis(pyvjoy.HID_USAGE_X, AXIS_CENTER)
    device.set_axis(pyvjoy.HID_USAGE_Y, AXIS_MIN)
    device.set_axis(pyvjoy.HID_USAGE_Z, AXIS_MIN)
    device.set_button(BUTTON_GEAR_UP, 0)
    device.set_button(BUTTON_GEAR_DOWN, 0)
    device.set_button(BUTTON_HANDBRAKE, 0)


# --- Standalone test ---
if __name__ == "__main__":
    import time

    print("Connecting to vJoy device...")
    device = init_vjoy()
    print("Connected. Watch vJoy Monitor.")

    print("Centering steering...")
    set_steering(device, 0.0)
    time.sleep(1)

    print("Steering full left...")
    set_steering(device, -1.0)
    time.sleep(1)

    print("Steering full right...")
    set_steering(device, 1.0)
    time.sleep(1)

    print("Throttle 50%...")
    set_throttle(device, 0.5)
    time.sleep(1)

    print("Pressing gear up button...")
    set_gear_up(device, True)
    time.sleep(1)
    set_gear_up(device, False)

    print("Resetting all...")
    reset_all(device)
    print("Done.")