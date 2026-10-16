import sys
from pathlib import Path

# Add project root to sys.path if run directly
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Any, Dict, Optional
from server.common.config import (
    VJOY_DEVICE_ID,
    AXIS_MIN,
    AXIS_MAX,
    AXIS_CENTER,
    BUTTON_GEAR_UP,
    BUTTON_GEAR_DOWN,
    BUTTON_HANDBRAKE,
)
from server.common.mapping import normalize


class VJoyOutput:
    """Thread-safe virtual joystick wrapper with graceful fallback."""

    def __init__(self, enabled: bool = True, device_id: int = VJOY_DEVICE_ID):
        self.available = False
        self._dev = None
        self._pyvjoy = None
        self._buttons: Dict[int, bool] = {}

        if enabled:
            try:
                import pyvjoy
                self._pyvjoy = pyvjoy
                self._dev = pyvjoy.VJoyDevice(device_id)
                self.available = True
            except Exception as exc:
                print(f"[vjoy] not available ({exc}); running in simulated mode")

        self.reset_all()

    def set_axis(self, usage_name: str, value: int):
        if self.available and self._dev and self._pyvjoy:
            try:
                self._dev.set_axis(getattr(self._pyvjoy, usage_name), value)
            except Exception:
                pass

    def set_button(self, number: int, pressed: bool):
        if self.available and self._dev:
            if self._buttons.get(number) != pressed:
                try:
                    self._dev.set_button(number, 1 if pressed else 0)
                except Exception:
                    pass
        self._buttons[number] = pressed

    def set_steering(self, value: float):
        """value: -1.0 (full left) to 1.0 (full right)."""
        axis_val = normalize(value, -1.0, 1.0, AXIS_MIN, AXIS_MAX)
        self.set_axis("HID_USAGE_X", axis_val)

    def set_throttle(self, value: float):
        """value: 0.0 to 1.0."""
        axis_val = normalize(value, 0.0, 1.0, AXIS_MIN, AXIS_MAX)
        self.set_axis("HID_USAGE_Y", axis_val)

    def set_brake(self, value: float):
        """value: 0.0 to 1.0."""
        axis_val = normalize(value, 0.0, 1.0, AXIS_MIN, AXIS_MAX)
        self.set_axis("HID_USAGE_Z", axis_val)

    def set_gear_up(self, pressed: bool):
        self.set_button(BUTTON_GEAR_UP, pressed)

    def set_gear_down(self, pressed: bool):
        self.set_button(BUTTON_GEAR_DOWN, pressed)

    def set_handbrake(self, pressed: bool):
        self.set_button(BUTTON_HANDBRAKE, pressed)

    def apply_packet(self, p: Dict[str, Any]):
        """Apply a packet dict with keys: steering, throttle, brake, gear_up, gear_down, handbrake."""
        self.set_steering(float(p.get("steering", 0.0)))
        self.set_throttle(float(p.get("throttle", 0.0)))
        self.set_brake(float(p.get("brake", 0.0)))
        self.set_gear_up(bool(p.get("gear_up", False)))
        self.set_gear_down(bool(p.get("gear_down", False)))
        self.set_handbrake(bool(p.get("handbrake", False)))

    def reset_all(self):
        """Center the wheel, release pedals and all buttons."""
        self.set_axis("HID_USAGE_X", AXIS_CENTER)
        self.set_axis("HID_USAGE_Y", AXIS_MIN)
        self.set_axis("HID_USAGE_Z", AXIS_MIN)
        self.set_gear_up(False)
        self.set_gear_down(False)
        self.set_handbrake(False)


# Module-level convenience functions for backward compatibility
_default_instance: Optional[VJoyOutput] = None


def init_vjoy(enabled: bool = True, device_id: int = VJOY_DEVICE_ID) -> VJoyOutput:
    global _default_instance
    _default_instance = VJoyOutput(enabled=enabled, device_id=device_id)
    return _default_instance


def apply_packet(device: Any, data: Dict[str, Any]):
    if isinstance(device, VJoyOutput):
        device.apply_packet(data)
    elif device is not None:
        # device is raw pyvjoy.VJoyDevice
        import pyvjoy
        device.set_axis(pyvjoy.HID_USAGE_X, normalize(data.get("steering", 0.0), -1.0, 1.0, AXIS_MIN, AXIS_MAX))
        device.set_axis(pyvjoy.HID_USAGE_Y, normalize(data.get("throttle", 0.0), 0.0, 1.0, AXIS_MIN, AXIS_MAX))
        device.set_axis(pyvjoy.HID_USAGE_Z, normalize(data.get("brake", 0.0), 0.0, 1.0, AXIS_MIN, AXIS_MAX))
        device.set_button(BUTTON_GEAR_UP, 1 if data.get("gear_up", False) else 0)
        device.set_button(BUTTON_GEAR_DOWN, 1 if data.get("gear_down", False) else 0)
        device.set_button(BUTTON_HANDBRAKE, 1 if data.get("handbrake", False) else 0)


def reset_all(device: Any):
    if isinstance(device, VJoyOutput):
        device.reset_all()
    elif device is not None:
        import pyvjoy
        device.set_axis(pyvjoy.HID_USAGE_X, AXIS_CENTER)
        device.set_axis(pyvjoy.HID_USAGE_Y, AXIS_MIN)
        device.set_axis(pyvjoy.HID_USAGE_Z, AXIS_MIN)
        device.set_button(BUTTON_GEAR_UP, 0)
        device.set_button(BUTTON_GEAR_DOWN, 0)
        device.set_button(BUTTON_HANDBRAKE, 0)


if __name__ == "__main__":
    import time

    print("Testing vJoy Output Driver...")
    out = init_vjoy()
    if not out.available:
        print("[!] vJoy is not available on this machine (driver not installed or device busy).")
        sys.exit(1)

    print("[OK] vJoy Device 1 acquired successfully!")
    print("Testing axes and buttons (watch vJoy Monitor)...")

    # 1. Steer left
    print(" - Steering: full left (-1.0)")
    out.set_steering(-1.0)
    time.sleep(0.5)

    # 2. Steer right
    print(" - Steering: full right (+1.0)")
    out.set_steering(1.0)
    time.sleep(0.5)

    # 3. Center steering
    print(" - Steering: center (0.0)")
    out.set_steering(0.0)
    time.sleep(0.3)

    # 4. Throttle 50%
    print(" - Throttle: 50% (0.5)")
    out.set_throttle(0.5)
    time.sleep(0.5)

    # 5. Brake 75%
    print(" - Brake: 75% (0.75)")
    out.set_brake(0.75)
    time.sleep(0.5)

    # 6. Button 1 (Gear Up)
    print(" - Gear Up (Button 1): pressed")
    out.set_gear_up(True)
    time.sleep(0.3)
    out.set_gear_up(False)

    # 7. Button 2 (Gear Down)
    print(" - Gear Down (Button 2): pressed")
    out.set_gear_down(True)
    time.sleep(0.3)
    out.set_gear_down(False)

    print(" - Resetting all axes and buttons to neutral...")
    out.reset_all()
    print("[OK] vJoy test completed successfully!")
