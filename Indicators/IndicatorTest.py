import sys
from typing import List,Dict
import pandas as pd
import numpy as np

sys.path.append("../RawIndicators/")
sys.path.append("../")

from Candle import new_candle
from DataBuffer import DataBuffer

from Indicators import (
	RelativeStrengthIndex,
	BalanceOfPower,
	MoneyFlowIndex,
	ChaikinOscillator,
	MovingAverageConverganceDivergence)

from RawIndicators import (
	relative_strength_index,
	balance_of_power,
	money_flow_index,
	chaikin_oscillator,
	moving_average_convergance_divergance)

candle_period = 30
prev_volume = 0.0
running_volume = 100000.0

def update_current_candle(candle:Dict,
							new_data:Dict)->bool:
	"""Pass in the current row data to update the current candle. We keep
	updating until we reach the candle period at which point the the candle is
	pushed and a new clean candle is generated. Note we use the best ask price
	in every situation.
	Returns whether the candle has been completed and a new one is needed."""
	global prev_volume,running_volume,candle_period

	live_volume = 0
	if prev_volume == 0.0:
		prev_volume = new_data["total_traded_asset"]
	else:
		live_volume = new_data["total_traded_asset"] - prev_volume
		prev_volume = new_data["total_traded_asset"]

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


def arange_with_endpoint(data:np.array,step:int)->np.array:
    """Convenience function to get around the fact that the np.arange function
    doesnt consider the endpoint properly. They reccomend using linspace to
    solve this, but we need arange, so we manually consider the endpoint.
    Returns the arange results."""
    aranged = np.arange(0,data.shape[0],step=step)
    
    # Adjust for how np.arange fails to consider the endpoint
    if aranged[-1] < data.shape[0] and (aranged[-1]+step) < data.shape[0]:
        aranged =np.append(aranged,aranged[-1]+period)
    return aranged


def convert_ticker_to_candles(ticker:pd.DataFrame,
							  period:int=30)->pd.DataFrame:
	"""Generates a dataframe of candle data using the specified options. Prices
	used are the best_asks. Volumes are determined by messing with the 24hour
	traded volume that we get each second. We diff the volumes to see how it
	changes every second and then cumsum with an initial starting volume to
	generate the volume traded at every second.
	Parameters:
		ticker (pd.DataFrame): The raw price and voluem data collected
		period (int): This is the candle stick period in seconds.
	Returns a new dataframe which only contains the candlestick data."""
	prices = ticker["best_ask"].values

	seed_volume = 100000.0 
	volume_data = np.diff(ticker["total_traded_asset"].values)
	volume_data = np.cumsum(np.insert(volume_data,0,seed_volume))
	open_idx = arange_with_endpoint(data=ticker.index.values,step=period)
	close_idx = np.add(open_idx,period-1)

	opens = prices[open_idx]
	if close_idx[-1] > prices.shape[0]:
		closes = prices[close_idx[:-1]]
		closes = np.append(closes,prices[-1])
	else:
		closes = prices[close_idx]

	highs = []
	lows = []
	volumes = []
	elements = []

	for o,c in zip(open_idx,close_idx):
		# Add one because numpy indexing excludes the last
		temp = prices[o:c+1]
		if len(temp) < period:
			open_idx = open_idx[:-1]
			close_idx = close_idx[:-1]
			opens = opens[:-1]
			closes = closes[:-1]
			break
		highs.append(np.max(temp))
		lows.append(np.min(temp))
		volumes.append(np.sum(volume_data[o:c+1]))
		elements.append(len(temp))

	candles = pd.DataFrame()
	candles["index"] = np.array(open_idx,dtype=np.intc)
	candles["open"] = np.array(opens,dtype=np.float64)
	candles["close"] = np.array(closes,dtype=np.float64)
	candles["low"] = np.array(lows,dtype=np.float64)
	candles["high"] = np.array(highs,dtype=np.float64)
	candles["volume"] = np.array(volumes,dtype=np.float64)
	candles["elements"] = np.array(elements,dtype=np.intc)
	return candles


def main():
	ticker_data = pd.read_csv("../BTCUSDT_ticker.csv")
	ticker_data = ticker_data[["best_bid","best_ask","total_traded_asset"]]
	ticker_data = ticker_data.to_dict("records")

	current_candle = new_candle()
	candles = DataBuffer(max_size=500,
						 filename="candles.csv",
						 header=["open","high","low","close","volume","elements"])

	
	# -------------------------------------------------------
	# Initialize the iterative class based indicators.
	rsi_class_values = []
	rsi_class = RelativeStrengthIndex(period=18,
									  buy_threshold=30,
									  sell_threshold=70,
									  buffer_size=250)
	mfi_class_values = []
	mfi_class = MoneyFlowIndex(period=18,
							   buy_threshold=30,
							   sell_threshold=70,
							   buffer_size=250)
	bop_class_values = []
	bop_class = BalanceOfPower(period=18,
							   buy_threshold=-0.30,
							   sell_threshold=0.18,
							   derivative_resolution=6,
							   buffer_size=250)
	macd_class_values = []
	macd_class = MovingAverageConverganceDivergence(
							fast_period=9,
							slow_period=18,
							signal_period=6,
							buffer_size=250)
	macd_class_values = []
	macd_class = MovingAverageConverganceDivergence(
							fast_period=9,
							slow_period=18,
							signal_period=6,
							buffer_size=250)
	# chaikin_class_values = []
	# chaikin_class = ChaikinOscillator(
	# 						slow_period=18,
	# 						fast_period=3,
	# 						signal_period=9,
	# 						buffer_size=250)
	# -------------------------------------------------------
	
	ramp_up_candles = 100
	for data in ticker_data:
		# Only push a new candle if it is completed aka the full period.
		if update_current_candle(current_candle,data):
			candles.push(current_candle)
			rsi_class_values.append(rsi_class.next_value(candles.get_all()))
			mfi_class_values.append(mfi_class.next_value(candles.get_all()))
			bop_class_values.append(bop_class.next_value(candles.get_all()))
			macd_class_values.append(macd_class.next_value(candles.get_all()))
			# chaikin_class_values.append(chaikin_class.next_value(candles.get_all()))
			current_candle = new_candle()

	# -------------------------------------------------------
	# Compute the numpy indicators
	ticker_data = pd.read_csv("../BTCUSDT_ticker.csv")
	ticker_data = ticker_data[["best_bid","best_ask","total_traded_asset"]]
	candles_df = convert_ticker_to_candles(ticker_data,candle_period)
	candles_df.to_csv("../buffers/candles_df_debug.csv")

	rsi_np_values = list(relative_strength_index(candles_df,18))
	mfi_np_values = list(money_flow_index(candles_df,18))
	bop_np_values = list(balance_of_power(candles_df,18))
	macd,signal,_ = moving_average_convergance_divergance(candles_df["close"].values,9,18,6)
	macd_np_values = list(macd-signal)
	# chaikin_np_values = list(chaikin_oscillator(candles_df,18,3))
	# -------------------------------------------------------

	# Compare the indicator results
	print("RSI Test")
	rsiA = np.array(rsi_np_values[18:])
	rsiB = np.array(rsi_class_values[18:])
	np.testing.assert_allclose(rsiA,rsiB,rtol=1e-12)

	print("MFI Test")
	mfiA = np.array(mfi_np_values[18:])
	mfiB = np.array(mfi_class_values[18:])
	np.testing.assert_allclose(mfiA,mfiB,rtol=1e-12)

	print("BOP Test")
	bopA = np.array(bop_np_values[18:])
	bopB = np.array(bop_class_values[18:])
	np.testing.assert_allclose(mfiA,mfiB,rtol=1e-12)

	print("MACD Test")
	macdA = np.array(macd_np_values[23:])
	macdB = np.array(macd_class_values[23:])
	np.testing.assert_allclose(macdA,macdB,rtol=1e-12)

	print("Tests Passed!")

if __name__ == "__main__":
	main()