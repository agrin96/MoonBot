from __future__ import annotations
from typing import List,Dict,Any
import numpy as np

from .BaseIndicator import BaseIndicator
from DataBuffer import DataBuffer


class Derivative(BaseIndicator):
	def __init__(self,period:int,buffer_size:int=250,output:bool=False):
		super().__init__()
		self._period = period
		if output:
			self._indicator_buffer = DataBuffer(
				max_size=buffer_size,
				filename=F"derivative_{period}.csv",
				header=[F"derivative{period}"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period-1):
			self._indicator_buffer.push(np.nan)


	def next_value(self,data:List[float])->float:
		if len(data) < self._period:
			return self._indicator_buffer.get(-1)
		
		starting = data[-self._period]
		ending = data[-1]
		derivative = (ending - starting) / self._period
		self._indicator_buffer.push(derivative)

		return derivative


def next_simple_moving_average(data:List[float],period:int)->float:
	"""Given the raw period data, returns the next simple moving average 
	datapoint"""
	return np.sum(data[-period:]) / period


class SimpleMovingAverage(BaseIndicator):
	def __init__(self,period:int,buffer_size:int=250,output:bool=False):
		super().__init__()
		self._period = period
		if output:
			self._indicator_buffer = DataBuffer(max_size=buffer_size,
												filename=F"sma_{period}.csv",
												header=[F"sma{period}"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period-1):
			self._indicator_buffer.push(np.nan)

	def next_value(self,data:List[float])->float:
		if len(data) < self._period:
			return self._indicator_buffer.get(-1)

		sma = np.sum(data[-self._period:]) / self._period
		self._indicator_buffer.push(sma)

		return sma


class ExponentialMovingAverage(BaseIndicator):
	def __init__(self,
				 period:int,
				 smoothing:int=2,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		self._alpha = smoothing / (1 + period)
		self._period = period
		
		if output:
			self._indicator_buffer = DataBuffer(max_size=buffer_size,
									  filename=F"ema_{period}.csv",
									  header=[F"ema{period}"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period-1):
			self._indicator_buffer.push(np.nan)

	
	def next_value(self,data:List[float]):
		if len(data) < self._period:
			return self._indicator_buffer.get(-1)
		
		if np.isnan(self._indicator_buffer.get(-1)):
			temp = data[-self._period:]
			first_ema = np.sum(temp) / self._period

			self._indicator_buffer.push(first_ema)
			return first_ema
		
		latest_close = data[-1]
		prev_ema = self._indicator_buffer.get(-1)

		ema = (latest_close - prev_ema) * self._alpha + prev_ema
		self._indicator_buffer.push(ema)
		return ema


class AccumulationDistributionLine(BaseIndicator):
	def __init__(self,buffer_size:int=250,output:bool=False):
		super().__init__()
		if output:
			self._indicator_buffer = DataBuffer(max_size=buffer_size,
									  filename=F"adl.csv",
									  header=[F"adl"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)
	
	def next_value(self,candles:List[Dict])->float:
		latest = candles[-1]
		close_low = latest["close"]-latest["low"]
		high_close = latest["high"]-latest["close"]
		high_low = latest["high"]-latest["low"]
		
		try:
			money_flow_multiplier = (close_low - high_close) / high_low
		except:
			money_flow_multiplier = 0
		
		prev_adl = 0
		if self._indicator_buffer.current_size() != 0:
			prev_adl = self._indicator_buffer.get(-1)
		adl = money_flow_multiplier * latest["volume"]
		adl = prev_adl + adl

		self._indicator_buffer.push(adl)
		return adl	
	

class ChaikinOscillator(BaseIndicator):
	def __init__(self,
				 slow_period:int=18,
				 fast_period:int=3,
				 signal_period:int=9,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		# Purely for reporting
		self._fast_period = fast_period
		self._slow_period = slow_period
		self._signal_period = signal_period
		
		self._adl = AccumulationDistributionLine()
		self._fast_ema = ExponentialMovingAverage(fast_period)
		self._slow_ema = ExponentialMovingAverage(slow_period)
		self._signal_sma = SimpleMovingAverage(signal_period)

		if output:
			self._chaikin_buffer = DataBuffer(max_size=buffer_size)
			self._indicator_buffer = DataBuffer(max_size=buffer_size,
				filename=F"chaikin_fast{fast_period}_slow{slow_period}.csv",
				header=[F"chaikin"])
		else:
			self._chaikin_buffer = DataBuffer(max_size=buffer_size)
			self._indicator_buffer = DataBuffer(max_size=buffer_size)
	

	def next_value(self,candles:List[Dict])->float:
		self._adl.next_value(candles)

		fast_value = self._fast_ema.next_value(self._adl.get_indicator())
		slow_value = self._slow_ema.next_value(self._adl.get_indicator())
		chaikin = fast_value-slow_value
		self._chaikin_buffer.push(chaikin)

		signal_value = self._signal_sma.next_value(self._chaikin_buffer.get_all())
		signal_value = chaikin - signal_value
		self._indicator_buffer.push(signal_value)

		return chaikin


	def make_decision(self)->str:
		previous_value = self._indicator_buffer.get(-2)
		latest_value = self._indicator_buffer.get(-1)

		if latest_value > 0 and previous_value < 0:
			return "BUY"
		if latest_value < 0 and previous_value > 0:
			return "SELL"
		
		return "HOLD"


	def __str__(self):
		return F"Chaikin of Fast: {self._fast_period} Slow: {self._slow_period} Signal: {self._signal_period}"


class MovingAverageConverganceDivergence(BaseIndicator):
	def __init__(self,
				 fast_period:int=9,
				 slow_period:int=18,
				 signal_period:int=6,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		# Purely for reporting
		self._fast_period = fast_period
		self._slow_period = slow_period
		self._signal_period = signal_period

		self._fast_ema = ExponentialMovingAverage(fast_period)
		self._slow_ema = ExponentialMovingAverage(slow_period)
		self._signal_ema = ExponentialMovingAverage(signal_period)

		if output:
			self._macd_buffer = DataBuffer(max_size=buffer_size)
			self._indicator_buffer = DataBuffer(max_size=buffer_size,
				filename=F"macd_fast{fast_period}_slow{slow_period}.csv",
				header=[F"macd"])
		else:
			self._macd_buffer = DataBuffer(max_size=buffer_size)
			self._indicator_buffer = DataBuffer(max_size=buffer_size)


	def next_value(self,candles:List[Dict])->float:
		closes = [c["close"] for c in candles]
		
		fast_value = self._fast_ema.next_value(closes)
		slow_value = self._slow_ema.next_value(closes)
		
		macd = fast_value - slow_value
		self._macd_buffer.push(macd)
		
		signal_value = self._signal_ema.next_value(self._macd_buffer.get_all())
		signal_value = macd - signal_value
		self._indicator_buffer.push(signal_value)

		return signal_value

	
	def make_decision(self)->str:
		previous_value = self._indicator_buffer.get(-2)
		latest_value = self._indicator_buffer.get(-1)

		if latest_value > 0 and previous_value < 0:
			return "BUY"
		if latest_value < 0 and previous_value > 0:
			return "SELL"
		return "HOLD"

		
	def __str__(self):
		return F"MACD of Fast: {self._fast_period} Slow: {self._slow_period} Signal: {self._signal_period}"


class MoneyFlowIndex(BaseIndicator):
	def __init__(self,
				 period:int=18,
				 buy_threshold:float=30,
				 sell_threshold:float=70,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		self._period = period
		self._buyt = buy_threshold
		self._sellt = sell_threshold

		self._prev_typical_price = None
		self._positive_money = DataBuffer(max_size=period)
		self._negative_money = DataBuffer(max_size=period)
		self._index = 0
		if output:
			self._indicator_buffer = DataBuffer(
				max_size=buffer_size,
				filename=F"mfi_period{period}.csv",
				header=["mfi"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period):
			self._indicator_buffer.push(np.nan)


	def next_value(self,candles:List[Dict])->float:
		prices = candles[-1]["high"]+candles[-1]["low"]+candles[-1]["close"]
		typical_price = np.divide(prices,3)

		raw_money_flow = abs(typical_price*candles[-1]["volume"])

		# Build up the money buffers to the period size.
		if self._prev_typical_price is None:
			self._prev_typical_price = typical_price
			self._negative_money.push(0.0)
			self._positive_money.push(0.0)
		else:
			change = typical_price - self._prev_typical_price
			self._prev_typical_price = typical_price

			if change >= 0:
				self._positive_money.push(raw_money_flow)
				self._negative_money.push(0.0)
			if change < 0:
				self._positive_money.push(0.0)
				self._negative_money.push(abs(raw_money_flow))

		if len(candles) < self._period:
			return self._indicator_buffer.get(-1)

		# Once we have enough data points stored in positive and negative money
		period_positive_money = np.sum(self._positive_money.get_all())
		period_negative_money = np.sum(self._negative_money.get_all())
		if period_negative_money == 0:
			period_negative_money = 1

		money_flow_ratio = period_positive_money / period_negative_money
		mfi = 100 - 100/(1 + money_flow_ratio)

		self._indicator_buffer.push(mfi)
		return mfi

	
	def make_decision(self)->str:
		latest_value = self._indicator_buffer.get(-1)

		if latest_value <= self._buyt:
			return "BUY"
		if latest_value >= self._sellt:
			return "SELL"
		return "HOLD"

		
	def __str__(self):
		return F"MFI of Period: {self._period}"


class RelativeStrengthIndex(BaseIndicator):
	def __init__(self,
				 period:int=18,
				 buy_threshold:float=30,
				 sell_threshold:float=70,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		self._period = period
		self._buyt = buy_threshold
		self._sellt = sell_threshold

		self._losses = DataBuffer(max_size=period)
		self._gains = DataBuffer(max_size=period)

		self._prev_avg_gain = None
		self._prev_avg_loss = None

		if output:
			self._indicator_buffer = DataBuffer(
				max_size=buffer_size,
				filename=F"rsi_period{period}.csv",
				header=["rsi"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period):
			self._indicator_buffer.push(np.nan)


	def next_value(self,candles:List[Dict])->float:
		if len(candles) < 2:
			self._gains.push(0.0)
			self._losses.push(0.0)
			return self._indicator_buffer.get(-1)

		current = candles[-1]["close"]
		previous = candles[-2]["close"]
		price_change = current - previous

		# Build up the gain/loss buffers to the period size.	
		if price_change >= 0:
			self._gains.push(price_change)
			self._losses.push(0.0)
		if price_change < 0:
			self._gains.push(0.0)
			self._losses.push(abs(price_change))

		if len(candles) < self._period:
			return self._indicator_buffer.get(-1)
		
		# The first previous RS is just the average gain/loss
		if self._prev_avg_gain is None:
			self._prev_avg_gain = np.mean(self._gains.get_all())
			self._prev_avg_loss = np.mean(self._losses.get_all())
		else:
			old_gain = self._prev_avg_gain*(self._period-1)
			new_gain = (old_gain + self._gains.get(-1))/self._period
			self._prev_avg_gain = new_gain
			
			old_loss = self._prev_avg_loss*(self._period-1)
			new_loss = (old_loss + self._losses.get(-1))/self._period
			self._prev_avg_loss = new_loss

		rs_gain = self._prev_avg_gain
		rs_loss = self._prev_avg_loss
		if rs_loss == 0:
			rs_loss = 1

		rsi = 100 - 100/(1 + (rs_gain/rs_loss))

		self._indicator_buffer.push(rsi)
		return rsi

	
	def make_decision(self)->str:
		latest_value = self._indicator_buffer.get(-1)

		if latest_value <= self._buyt:
			return "BUY"
		if latest_value >= self._sellt:
			return "SELL"
		return "HOLD"

		
	def __str__(self):
		return F"RSI of Period: {self._period}"


class BalanceOfPower(BaseIndicator):
	def __init__(self,
				 period:int=18,
				 buy_threshold:float=-0.30,
				 sell_threshold:float=0.18,
				 derivative_resolution:int=6,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		self._period = period
		self._buyt = buy_threshold
		self._sellt = sell_threshold
		self._detivative_resoluton = derivative_resolution

		self._sma = SimpleMovingAverage(period,buffer_size=250)
		self._raw_bop = DataBuffer(max_size=period)
		self._derivative = Derivative(derivative_resolution,period)

		if output:
			self._indicator_buffer = DataBuffer(
				max_size=buffer_size,
				filename=F"bop_period{period}.csv",
				header=["bop"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period):
			self._indicator_buffer.push(np.nan)


	def next_value(self,candles:List[Dict])->float:
		latest = candles[-1]
		close_open = latest["close"]-latest["open"]
		high_low = latest["high"]-latest["low"]
		try:
			value = close_open / high_low
		except:
			value = np.nan
		self._raw_bop.push(value)
		
		bop_sma = None
		if self._period > 1:
			bop_sma = self._sma.next_value(self._raw_bop.get_all())

		if len(self._sma.get_indicator()) < self._period-1:
			return self._indicator_buffer.get(-1)

		self._indicator_buffer.push(bop_sma)
		self._derivative.next_value(self._indicator_buffer.get_all())

		return self._indicator_buffer.get(-1)

	
	def make_decision(self)->str:
		latest_bop = self._indicator_buffer.get(-1)
		latest_derivative = self._derivative.get_indicator()[-1]

		if latest_bop <= self._buyt and latest_derivative < 0:
			return "BUY"
		if latest_bop >= self._sellt and latest_derivative > 0:
			return "SELL"
		return "HOLD"

	
	def __str__(self):
		return F"BOP of Period: {self._period} Derivative: {self._detivative_resoluton}"


class StochasticOscillator(BaseIndicator):
	def __init__(self,
				 period:int=14,
				 signal_period:int=3,
				 buy_threshold:float=20,
				 sell_threshold:float=80,
				 buffer_size:int=250,
				 output:bool=False):
		super().__init__()
		self._period = period
		self._buyt = buy_threshold
		self._sellt = sell_threshold

		self._highs = DataBuffer(max_size=period)
		self._lows = DataBuffer(max_size=period)

		self._raw_stochastic =DataBuffer(max_size=120)
		self._sma = SimpleMovingAverage(signal_period,buffer_size=signal_period)

		if output:
			self._indicator_buffer = DataBuffer(
				max_size=buffer_size,
				filename=F"stochastic_period{period}.csv",
				header=["stochastic"])
		else:
			self._indicator_buffer = DataBuffer(max_size=buffer_size)

		for _ in range(period-1):
			self._indicator_buffer.push(np.nan)


	def next_value(self,candles:List[Dict])->float:
		latest = candles[-1]
		self._highs.push(latest["high"])
		self._lows.push(latest["low"])

		if len(candles) < self._period:
			return self._indicator_buffer.get(-1)

		lowest_low = np.min(self._lows.get_all())
		highest_high = np.max(self._highs.get_all())

		stochastic = (latest["close"]-lowest_low)/(highest_high-lowest_low)*100

		self._raw_stochastic.push(stochastic)
		percentD = self._sma.next_value(self._raw_stochastic.get_all())

		self._indicator_buffer.push(percentD)
		return percentD

	
	def make_decision(self)->str:
		latest_value = self._indicator_buffer.get(-1)

		if latest_value <= self._buyt:
			return "BUY"
		if latest_value >= self._sellt:
			return "SELL"
		return "HOLD"

		
	def __str__(self):
		return F"Stochastic of Period: {self._period}"
