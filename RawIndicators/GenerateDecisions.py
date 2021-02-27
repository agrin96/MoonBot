from __future__ import annotations
from typing import List
import pandas as pd
import numpy as np

from .RawIndicators import (
    balance_of_power,
    derivative,
    relative_strength_index,
    money_flow_index,
    chaikin_oscillator,
    simple_moving_average,
    array_shift,
    moving_average_convergance_divergance)

def generate_bop_decisions(candles:pd.DataFrame,
                           buy_threshold:float=-0.24,
                           sell_threshold:float=0.18,
                           period:int=18,
                           derivative_resolution:int=6)->List[str]:
    """Generates a set of decisions based on the balance of power and its
    derivative which tells us whether we are increasing or decreasing. Note that
    the buy and sell thresholds are different for different commodities and 
    should be experimentally determined.
    Parameters:
        buy_threshold (float): The threshold at which to consider a buy signal
        sell_threshold (float): The threshold at which to consider a sell signal
    Returns the list of decisions."""
    bop = balance_of_power(candles,period)
    
    bop_prime = derivative(bop,derivative_resolution)
    bop_prime = np.where(np.isnan(bop_prime),0,bop_prime)

    decisions = np.where((bop_prime<0)&(bop<=buy_threshold),"BUY",'HOLD')
    decisions = np.where((bop_prime>0)&(bop>=sell_threshold),"SELL",decisions)
    
    return decisions


def generate_rsi_decisions(candles:pd.DataFrame,
                           buy_threshold:float=30,
                           sell_threshold:float=70,
                           period:int=18)->List[str]:
    """Generates a set of decisions based on the relative strength index. Note 
    that the buy and sell thresholds are different for different commodities and 
    should be experimentally determined.
    Parameters:
        buy_threshold (float): The threshold at which to consider a buy signal
        sell_threshold (float): The threshold at which to consider a sell signal
    Returns the list of decisions."""
    rsi = relative_strength_index(candles,period)

    decisions = np.where(rsi<=buy_threshold,"BUY",'HOLD')
    decisions = np.where(rsi>=sell_threshold,"SELL",decisions)

    return decisions


def generate_mfi_decisions(candles:pd.DataFrame,
                           buy_threshold:float=30,
                           sell_threshold:float=70,
                           period:int=18)->List[str]:
    """Generates a set of decisions based on the money flow index. Note 
    that the buy and sell thresholds are different for different commodities and 
    should be experimentally determined.
    Parameters:
        buy_threshold (float): The threshold at which to consider a buy signal
        sell_threshold (float): The threshold at which to consider a sell signal
    Returns the list of decisions."""
    mfi = money_flow_index(candles,period)

    decisions = np.where(mfi<=buy_threshold,"BUY",'HOLD')
    decisions = np.where(mfi>=sell_threshold,"SELL",decisions)

    return decisions


def generate_chaikin_decisions(candles:pd.DataFrame,
                               fast_period:int,
                               slow_period:int,
                               signal_period:int)->List[str]:
    """Generates a set of decisions based on the chaikin oscillator subtracted
    from its simple moving average. When this measure moves from negative to
    positive its a buy signal, and from positive to negative a sell signal.
    We determine this move by shifting the signal back and comparing it with
    its older values.
    Returns the list of decisions."""
    chaikin = chaikin_oscillator(candles,slow_period,fast_period)
    sma = simple_moving_average(chaikin,signal_period)
    
    signal = chaikin - sma
    shifted = array_shift(signal,1)

    decisions = np.where((signal > 0) & (shifted < 0),"BUY",'HOLD')
    decisions = np.where((signal < 0) & (shifted > 0),"SELL",decisions)

    return decisions


def generate_macd_decisions(candles:pd.DataFrame,
                            fast_period:int,
                            slow_period:int,
                            signal_period:int)->List[str]:
    """Generates a set of decisions based on the MACD subtracted from its 
    signal line. When this measure moves from negative to positive its a buy 
    signal, and from positive to negative a sell signal.We determine this move 
    by shifting the signal back and comparing it with its older values
    Returns the list of decisions."""
    macd,signal,indicator = moving_average_convergance_divergance(
        data=candles["close"],
        fast_window=fast_period,
        slow_window=slow_period,
        signal_window=signal_period)

    shifted = array_shift(indicator,1)

    decisions = np.where((indicator > 0) & (shifted < 0),"BUY",'HOLD')
    decisions = np.where((indicator < 0) & (shifted > 0),"SELL",decisions)

    return decisions


def generate_stochastic_decisions(candles:pd.DataFrame,
                                  buy_threshold:float=20,
                                  sell_threshold:float=80,
                                  period:int=3):
    indicator = stochastic_oscillator(candles,period)

    decisions = np.where(indicator > sell_threshold,"SELL",'HOLD')
    decisions = np.where(indicator < buy_threshold,"BUY",decisions)

    return decisions
