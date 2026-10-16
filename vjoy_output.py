"""Backward-compatibility proxy for server.common.vjoy_output."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.common.vjoy_output import *  # noqa: F401, F403

if __name__ == "__main__":
    from server.common.vjoy_output import init_vjoy, reset_all
    import time

    print("Testing vJoy output via server/common/vjoy_output.py...")
    dev = init_vjoy()
    print("vJoy Available:", getattr(dev, "available", True))
    reset_all(dev)
    print("Reset completed.")
