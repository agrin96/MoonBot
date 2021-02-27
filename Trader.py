from typing import Dict,List,Any
import asyncio
import websockets
import json
from datetime import datetime,timezone
from time import time
from dataclasses import dataclass,field
import os

from DataBuffer import DataBuffer
from Candle import new_candle,update_current_candle
from TreeActions import evaluate_next_value,make_tree_decision
from TreeIO import deserialize_tree
from TradeConfiguration import TradingConfiguration
from Reporting import live_trade_report

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

trade_state = TradingConfiguration(candle_period=30,build_period=0)


def parse_ticker_data_row(data:Dict)->Dict:
    """Expand the returned ticker names and use them to get data we want."""
    return {v:data[k] for k,v in ticker_mapping.items()}


def make_trading_decision(ticker:Dict):
    """Generate next decision if it is valid to do so."""
    global trade_state
    evaluate_next_value(node=trade_state.tree,
                        candles=trade_state.candle_buffer.get_all())

    if trade_state.candle_buffer.current_size() > trade_state.build_period:
        decision = make_tree_decision(trade_state.tree)
        print(F"Decision made: {decision}\n")

        if trade_state.prev_decision == "SELL" and decision == "BUY":
            # Simulated balance as if we sold now
            trade_state.coin_balance =\
                (trade_state.current_balance / float(ticker["best_ask"]))\
                    *trade_state.fee
            trade_state.bought_balance = trade_state.current_balance
            
            trade_state.prev_decision = "BUY"
            print("--------------------------------------")
            print("Made a BUY trade")
            print("--------------------------------------")
            return

        if trade_state.prev_decision == "BUY" and decision == "SELL":
            trade_state.current_balance =\
                (trade_state.coin_balance * float(ticker["best_bid"]))\
                    *trade_state.fee

            trade_state.coin_balance = 0.0

            if trade_state.bought_balance > trade_state.current_balance:
                trade_state.lose_trades += 1
            elif trade_state.bought_balance < trade_state.current_balance:
                trade_state.gain_trades += 1

            trade_state.prev_decision = "SELL"
            print("--------------------------------------")
            print("Made a SELL trade")
            print("--------------------------------------")
            return


async def trader(ws,ticker:str):
    global trade_state
    
    period_counter = 0
    while True:
        data = json.loads(await ws.recv())
        start_t = time()

        if data["stream"] == ticker+"@ticker":
            print(F"Next Candle: {period_counter}/{trade_state.candle_period}")
            period_counter += 1
            if period_counter == trade_state.candle_period:
                period_counter = 0
            
            ticker_data = parse_ticker_data_row(data["data"])
            live_trade_report(trade_state,ticker_data)

            if update_current_candle(trade_state,ticker_data):
                print("!--------- Pushing New Candle ------------!")
                trade_state.candle_buffer.push(trade_state.current_candle)
                trade_state.current_candle = new_candle()
                make_trading_decision(ticker_data)


async def keep_alive(ws):
    """Binance expects a pong sent every 3 minutes to keep alive."""
    print("Starting keep alive")
    while True:
        await asyncio.sleep(120)
        print("Sending Pong")
        await ws.pong()


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