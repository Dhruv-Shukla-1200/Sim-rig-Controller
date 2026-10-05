# mapping.py — value normalization and calibration logic.
# Keep anything related to "how a raw input value becomes an axis value"
# here, separate from vJoy-specific code.

def normalize(value, in_min, in_max, out_min, out_max):
    """Map a value from one range to another, clamping to in_min/in_max first."""
    value = max(in_min, min(in_max, value))
    ratio = (value - in_min) / (in_max - in_min)
    return int(ratio * (out_max - out_min) + out_min)