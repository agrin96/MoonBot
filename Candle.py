from __future__ import annotations
from typing import Dict
import numpy as np

def new_candle()->Dict:
    """Returns a totally new reset candle with no information filled in yet."""
    return {"open":None,
            "high":-np.inf,
            "low":np.inf,
            "close":None,
            "volume":0.0,
            "elements":0}