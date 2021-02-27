from typing import Dict,List,Any
import asyncio
import websockets
import json
from datetime import datetime,timezone
from time import time
import os

from DataBuffer import DataBuffer
from Candle import new_candle
from TreeActions import evaluate_next_value,make_tree_decision
from TreeIO import deserialize_tree

tickers = [
    "btcusdt"
]

stream_subscribe = {
    "method": "SUBSCRIBE",
    "params": [t+"@ticker" for t in tickers],
    "id": 1
}
stream_unsubscribe = {
    "method": "UNSUBSCRIBE",
    "params": [t+"@ticker" for t in tickers],
    "id": 2
}
ticker_mapping = {
    "b":"best_bid",
    "a":"best_ask",
    "w":"total_traded_asset"
}

raw_stream_uri = "wss://stream.binance.com:9443/ws"
combined_stream_uri = "wss://stream.binance.com:9443/stream"


def parse_ticker_data_row(data:Dict)->Dict:
    """Expand the returned ticker names and use them to get data we want."""
    return {v:data[k] for k,v in ticker_mapping.items()}


async def keep_alive(ws):
    """Binance expects a pong sent every 3 minutes to keep alive."""
    print("Starting keep alive")
    while True:
        await asyncio.sleep(120)
        print("Sending Pong")
        await ws.pong()


candle_buffer = DataBuffer(max_size=300,
                           filename="btcusdt_candles.csv",
                           header=["open","high","low","close","volume","elements"])
prev_volume = 0.0
running_volume = 100000.0
candle_period = 30
ramp_up_period = 0
current_candle = new_candle()
first_price = None

tree = None
with open("./SerializedTrees/popfile-0.json") as file:
    tree = deserialize_tree(file.read())

current_balance = 100.0
coin_balance = 0.0
prev_decision = "SELL"
num_trades = 0


def update_current_candle(candle:Dict,
                          new_data:Dict)->bool:
    """Pass in the current row data to update the current candle. We keep
    updating until we reach the candle period at which point the the candle is
    pushed and a new clean candle is generated. Note we use the best ask price
    in every situation.
    Returns whether the candle has been completed and a new one is needed."""
    global prev_volume,running_volume,candle_period
    live_volume = 0.0
    if prev_volume == 0.0:
        prev_volume = float(new_data["total_traded_asset"])
    else:
        live_volume = float(new_data["total_traded_asset"]) - prev_volume
        prev_volume = float(new_data["total_traded_asset"])

    running_volume += live_volume

    if candle["open"] is None:
        candle["open"] = float(new_data["best_ask"])

    if candle["high"] < float(new_data["best_ask"]):
        candle["high"] = float(new_data["best_ask"])

    if candle["low"] > float(new_data["best_ask"]):
        candle["low"] = float(new_data["best_ask"])

    candle["volume"] += running_volume
    candle["close"] = float(new_data["best_ask"])
    candle["elements"] += 1

    if candle["elements"] == candle_period:
        return True

    return False


async def trader(ws,ticker:str):
    global current_candle,indicator,current_balance
    global coin_balance,ramp_up_period,prev_decision,num_trades

    global first_price
    
    period_counter = 0
    while True:
        data = json.loads(await ws.recv())
        start_t = time()

        if data["stream"] == ticker+"@ticker":
            print(F"Fetched ticker data: {period_counter}/{candle_period}")
            period_counter += 1
            if period_counter == candle_period:
                period_counter = 0
            
            ticker_data = parse_ticker_data_row(data["data"])
            
            # Produce a live balance that gets updated every tick.
            if coin_balance != 0.0:
                temp = (coin_balance * float(ticker_data["best_bid"]))*0.999
                print(F"Appx Balance: {temp}, Coins: {coin_balance}")
            else:
                print(F"Current Balance: {current_balance}, Coins: {coin_balance}")

            # Prints the baseline balance of holding long for comparison
            if first_price is None:
                first_price = float(ticker_data["best_ask"])
            else:
                temp = (100.0 / first_price)*0.999
                long = (temp * float(ticker_data["best_bid"]))*0.999
                print(F"Baseline Balance: {long}\n")

            if update_current_candle(current_candle,
                                     ticker_data):
                print("!----Pushing New Candle.")
                candle_buffer.push(current_candle)
                current_candle = new_candle()

                evaluate_next_value(tree,candle_buffer.get_all())
                if candle_buffer.current_size() > ramp_up_period:
                    decision = make_tree_decision(tree)
                    
                    if prev_decision == "SELL" and decision == "BUY":
                        coin_balance = (current_balance / float(ticker_data["best_ask"]))*0.999
                        # Simulated balance as if we sold now
                        current_balance = (coin_balance * float(ticker_data["best_bid"]))*0.999
                        
                        prev_decision = "BUY"
                        print("--------------------------------------")
                        print("Made a BUY trade")
                        print("\tCurrent Balance: ",current_balance)
                        print("\tNumber of Trades: ",num_trades)
                        print("--------------------------------------")
                        continue

                    if prev_decision == "BUY" and decision == "SELL":
                        current_balance = (coin_balance * float(ticker_data["best_bid"]))*0.999
                        coin_balance = 0.0

                        prev_decision = "SELL"
                        num_trades += 1

                        print("--------------------------------------")
                        print("Made a SELL trade")
                        print("\tCurrent Balance: ",current_balance)
                        print("\tNumber of Trades: ",num_trades)
                        print("--------------------------------------")
                        continue          


async def stream_connection():
    while True:
        try:
            async with websockets.connect(combined_stream_uri,ping_interval=None) as ws:
                await ws.send(json.dumps(stream_subscribe))
                
                res = json.loads(await ws.recv())
                if res != {"result": None,"id": 1}:
                    print(F"Invalid response on subscribe {res}")
                    raise RuntimeError

                await asyncio.gather(keep_alive(ws),trader(ws,"btcusdt"))

                res = await ws.send(json.dumps(stream_unsubscribe))
        except Exception as e:
            print(F"Encountered error: {e}")
            print("Restarting socket connection...")
            continue

asyncio.run(stream_connection())