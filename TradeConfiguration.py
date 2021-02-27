from DataBuffer import DataBuffer
from typing import Dict
from Candle import new_candle
from TreeIO import deserialize_tree
from dataclasses import dataclass,field

@dataclass
class TradingConfiguration:
    """Running Parameters for building our candles and storing the state."""
    first_price:float = None
    initial_coin_balance:float = None

    prev_volume:float = 0.0
    running_volume:float = 100000.0
    candle_period:int = 30
    build_period:int = 0
    current_candle:Dict = field(default_factory=new_candle)
    
    current_balance:float = 100.0
    bought_balance:float = 0.0
    coin_balance:float = 0.0
    prev_decision:str = "SELL"
    gain_trades:int = 0
    lose_trades:int = 0
    
    # Default is 0.001
    commission:float = 0.01
    fee:float = 1 - commission

    tree = None
    with open("./SerializedTrees/popfile-0.json") as file:
        tree = deserialize_tree(file.read())

    candle_buffer = DataBuffer(max_size=candle_period*2,
        filename="trade_candles.csv",
        header=["open","high","low","close","volume","elements"])