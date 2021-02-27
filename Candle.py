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


def update_current_candle(state,
                          new_data:Dict)->bool:
    """Pass in the current row data to update the current candle. We keep
    updating until we reach the candle period at which point the the candle is
    pushed and a new clean candle is generated. Note we use the best ask price
    in every situation.
    Returns whether the candle has been completed and a new one is needed."""
    live_volume = 0.0
    if state.prev_volume == 0.0:
        state.prev_volume = float(new_data["total_traded_asset"])
    else:
        live_volume = float(new_data["total_traded_asset"]) - state.prev_volume
        state.prev_volume = float(new_data["total_traded_asset"])

    state.running_volume += live_volume

    if state.current_candle["open"] is None:
        state.current_candle["open"] = float(new_data["best_ask"])

    if state.current_candle["high"] < float(new_data["best_ask"]):
        state.current_candle["high"] = float(new_data["best_ask"])

    if state.current_candle["low"] > float(new_data["best_ask"]):
        state.current_candle["low"] = float(new_data["best_ask"])

    state.current_candle["volume"] += state.running_volume
    state.current_candle["close"] = float(new_data["best_ask"])
    state.current_candle["elements"] += 1

    if state.current_candle["elements"] == state.candle_period:
        return True
    return False