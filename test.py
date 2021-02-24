from __future__ import annotations
from typing import List,Any
import numpy as np
import pandas as pd
import json

from Candle import new_candle
from DataBuffer import DataBuffer
from Indicators.Indicators import ChaikinOscillator,MovingAverageConverganceDivergence
from TreeActions import pprint_tree,make_tree_decision,evaluate_next_value
from TreeIO import deserialize_tree

candle_period = 30
prev_volume = 0.0
running_volume = 0

def update_current_candle(candle:Dict,
							new_data:Dict)->bool:
	"""Pass in the current row data to update the current candle. We keep
	updating until we reach the candle period at which point the the candle is
	pushed and a new clean candle is generated. Note we use the best ask price
	in every situation.
	Returns whether the candle has been completed and a new one is needed."""
	global prev_volume
	global running_volume
	
	live_volume = new_data["total_traded_usdt"] - prev_volume

	prev_volume = new_data["total_traded_usdt"]
	running_volume += live_volume

	if candle["open"] is None:
		candle["open"] = new_data["best_ask"]

	if candle["high"] < new_data["best_ask"]:
		candle["high"] = new_data["best_ask"]

	if candle["low"] > new_data["best_ask"]:
		candle["low"] = new_data["best_ask"]

	candle["volume"] += running_volume
	candle["close"] = new_data["best_ask"]
	candle["elements"] += 1

	if candle["elements"] == candle_period:
		return True

	return False


def main():
	tree = None
	with open("./SerializedTrees/popfile-0.json") as file:
		tree = deserialize_tree(file.read())

	training_data = pd.read_csv("BTCUSDT_ticker.csv")
	training_data = training_data[["best_bid","best_ask","total_traded_usdt"]]
	training_data = training_data.to_dict("records")

	current_candle = new_candle()

	candles = DataBuffer(max_size=500,
						 filename="candles.csv",
						 header=["open","high","low","close","volume","elements"])

	ramp_up_candles = 100
	# ramp_up_candles = 217
	decisions = []
	for data in training_data:
		if update_current_candle(current_candle,data):
			candles.push(current_candle)

			evaluate_next_value(tree,candles.get_all())
			if candles.current_size() > ramp_up_candles:
				decisions.append(make_tree_decision(tree))
			current_candle = new_candle()

	print("Decisions Made: ",len(decisions))
	print(decisions)
	print("Total: ",candles.current_size())

	return decisions


def test_deserialization():
	from TreeIO import deserialize_tree

	with open("./SerializedTrees/popfile-0.json") as file:
		tree = deserialize_tree(file.read())
		print(tree)
		pprint_tree(tree)


if __name__ == "__main__":
	# test_deserialization()
	main()