from typing import List,Dict,Any

import pandas as pd
import numpy as np
from test import main

def simple_moving_average(data:np.array,period:int)->np.array:
    """Implementation of a simple moving average for numpy using convolutions."""
    sums = np.convolve(data,np.ones(period),'valid')[:data.shape[0]]
    sma = sums / period
    sma = np.append(np.repeat(np.nan,period-1),sma)
    return sma
    

def array_shift(arr:np.array,num:int)->np.array:
    """Shifts the arrray values and pads with nans as necessary."""
    new = np.empty_like(arr)
    if num >= 0:
        # Shifts the values forward and cuts the end
        new[:num] = np.nan
        new[num:] = arr[:-num]
    else:
        # Shifts the values back and appends nans.
        new[num:] = np.nan
        new[:num] = arr[-num:]
    return new


def exponential_moving_average(
        data:np.array,
        period:int,
        smoothing:int=2)->np.array:
    """Calculates the exponential moving average. Implemented from
    https://www.investopedia.com/terms/e/ema.asp
    Parameters:
        period (int): The number of lags to use in the moving average.
        smoothing (int): Used for alpha constant, determines smooth the ma
            will be."""

    alpha = (smoothing / (1+period))
    # If nans, figure out the index of all the nans and offset by that.
    offset = np.sum(np.where(np.isfinite(data),0,1))
    prices = data[offset:]

    seed_value = np.mean(prices[:period])
    ema = np.array([*np.repeat(np.nan,period-1+offset),seed_value])

    for i in range(period,prices.shape[0]):
        prev_ema = ema[-1]
        close = prices[i]
        ema = np.append(ema,(close - prev_ema) * alpha + prev_ema)
    return ema


def accumulation_distribution_line(data:pd.DataFrame)->np.array:
    """The ADL measures the cummulative flow of money into and out of the system
    The main tell point is when the indicator diverges from the price.
    Implemented From:
    https://school.stockcharts.com/doku.php?id=technical_indicators:accumulation_distribution_line
    """
    money_flow_multiplier =\
        ((data["close"]-data["low"]) - (data["high"]-data["close"]))\
            / (data["high"]-data["low"])
    money_flow_volume = np.multiply(data["volume"].values,money_flow_multiplier)
    
    return np.cumsum(money_flow_volume)


def chaikin_oscillator(data:pd.DataFrame,
                       slow_period:int=10,
                       fast_period:int=3)->np.array:
    """The chaikin oscillator shows buying pressure prevailing when it is 
    positive and selling pressure prevailing when it is negative. Crosses
    indicate a change in the behavior.
    Returns the chaikin oscillator for each candle period."""
    adl = accumulation_distribution_line(data)
    fast = exponential_moving_average(adl,fast_period)
    slow = exponential_moving_average(adl,slow_period)
    return fast - slow


def generate_chaikin_decisions(candles:pd.DataFrame)->List[str]:
    """Generates a set of decisions based on the chaikin oscillator subtracted
    from its simple moving average. When this measure moves from negative to
    positive its a buy signal, and from positive to negative a sell signal.
    We determine this move by shifting the signal back and comparing it with
    its older values.
    Returns the list of decisions."""
    chaikin = chaikin_oscillator(candles,18,3)
    sma = simple_moving_average(chaikin,9)
    
    signal = chaikin - sma
    shifted = array_shift(signal,1)

    decisions = np.where((signal > 0) & (shifted < 0),"BUY",'HOLD')
    decisions = np.where((signal < 0) & (shifted > 0),"SELL",decisions)

    return list(decisions)


def moving_average_convergance_divergance(
        data:np.array,fast_window:int,slow_window:int,signal_window:int):
    """Calculate the moving average convergance divergance. Momentum indicator
    which operates on the interaction between the MACD line and the Signal line.
    Implemented following: https://www.investopedia.com/terms/m/macd.asp
    
    Parameters:
        fast_window (int): The lags to use for the more reactive line
        slow_window (int): The lags to use for the more stable line. Should be
            more than for the fast window.
        signal_window (int): The window to use over the macd line to compare
            against. Should be less than both the others.

    Returns MACD,Signal,Histogram
    """
    fast = exponential_moving_average(data=data,period=fast_window)
    slow = exponential_moving_average(data=data,period=slow_window)
    macd_line = fast - slow
    signal = exponential_moving_average(data=macd_line,period=signal_window)
    histogram = macd_line - signal

    return macd_line,signal,histogram


def generate_macd_decisions(candles:pd.DataFrame)->List[str]:
    """Generates a set of decisions based on the MACD subtracted from its 
    signal line. When this measure moves from negative to positive its a buy 
    signal, and from positive to negative a sell signal.We determine this move 
    by shifting the signal back and comparing it with its older values
    Returns the list of decisions."""
    # macd,signal,histogram = moving_average_convergance_divergance(
    #     data=candles["close"],
    #     fast_window=12,
    #     slow_window=26,
    #     signal_window=9)
    macd,signal,histogram = moving_average_convergance_divergance(
        data=candles["close"],
        fast_window=9,
        slow_window=18,
        signal_window=6)
    
    indicator = macd - signal
    shifted = array_shift(indicator,1)
    for i in indicator[217:]:
        print(i)
    decisions = np.where((indicator > 0) & (shifted < 0),"BUY",'HOLD')
    decisions = np.where((indicator < 0) & (shifted > 0),"SELL",decisions)

    return list(decisions)


def compare():
    decisionsB = main()

    # ramp_up_period = 100
    ramp_up_period = 217
    candles = pd.read_csv("./buffers/candles.csv")

    # decisionsA = generate_chaikin_decisions(candles)[ramp_up_period:]
    decisionsA = generate_macd_decisions(candles)[ramp_up_period:]

    print("Old method")
    print(decisionsA)
    print("new method")
    print(decisionsB)
    # print("Are they equal: ", decisionsA==decisionsB)
    print("Sizes: ")
    print("New",len(decisionsB))
    print("Old",len(decisionsA))
    print(decisionsA==decisionsB)



if __name__ == "__main__":
    compare()