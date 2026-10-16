"""Value normalization and calibration logic."""


def normalize(value: float, in_min: float, in_max: float, out_min: int, out_max: int) -> int:
    """Map a value from [in_min, in_max] to [out_min, out_max], with clamping."""
    value = max(in_min, min(in_max, float(value)))
    ratio = (value - in_min) / (in_max - in_min)
    return int(ratio * (out_max - out_min) + out_min)
