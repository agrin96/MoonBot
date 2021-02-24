import pandas as pd
import numpy as np

def derivative(arr:np.array,resolution:int)->np.array:
    """Computes a dumb derivative by taking the slope between each set of 
    values in the input array. The resolution specifies the interval of the
    derivativev computation. This function preserves array shape."""
    diffs = arr - array_shift(arr,resolution)
    return diffs / resolution


def integral(arr:np.array,resolution:int,samples:int)->np.array:
    """Garbage function"""
    Xs = np.arange(0,arr.shape[0],dtype=np.float64)\
         if arr.shape[0] % 2 == 0\
         else np.arange(0,arr.shape[0]+1,dtype=np.float64)

    # Create N number of points between each consecutive 2 points.
    shifted = array_shift(Xs,num=-1)
    shifted = np.where(np.isfinite(shifted),shifted,0)

    new_points = np.linspace(Xs[:-1],shifted[:-1],samples,endpoint=True)
    new_points = new_points.T.reshape(1,-1).flatten()
    mask = np.ones_like(new_points,dtype=bool)
    mask[::3] = 0
    mask[0] = 1

    # Find the Y value at each of the new points
    new_data = np.interp(new_points[mask],Xs[:-1],arr)
    return np.nancumsum(new_data / samples)



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


def rescale(arr:np.array,low:int,high:int)->np.array:
    """Rescales the data to the desired range"""
    omax = np.nanmax(arr)
    omin = np.nanmin(arr)
    return (high-low)/(omax-omin)*(arr-omax)+high


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


def simple_moving_average(data:np.array,period:int)->np.array:
    """Implementation of a simple moving average for numpy using convolutions."""
    sums = np.convolve(data,np.ones(period),'valid')[:data.shape[0]]
    sma = sums / period
    sma = np.append(np.repeat(np.nan,period-1),sma)
    return sma


def hull_moving_average(close_data:np.array,period:int)->np.array:
    """Hull moving averages have a lower lag compared to other types. Using as
    3 stop exponential moving average. Implemented from:
    https://school.stockcharts.com/doku.php?id=technical_indicators:hull_moving_average
    """
    eMA1 = exponential_moving_average(close_data,period//2)
    eMA2 = exponential_moving_average(close_data,period)
    raw_hMA = (2*eMA1)-eMA2
    return exponential_moving_average(raw_hMA,int(np.sqrt(period)))


def kaufman_adaptive_moving_average(data:np.array,
                                    er_period:int,
                                    fast_ema:int,
                                    slow_ema:int)->np.array:
    """KAMA is a technique that adapts to the volatility of the market. If there
    are many swings then KAMA follows them closely, if there are few then it
    relaxes and follow from a distance. Implemented from
    https://school.stockcharts.com/doku.php?id=technical_indicators:kaufman_s_adaptive_moving_average
    """
    change = np.abs(data-array_shift(data,er_period))
    
    volatility = np.abs(data-array_shift(data,1))
    volatility = np.convolve(volatility,np.ones(er_period,dtype=int),'valid')
    volatility = np.append(np.repeat(np.nan,er_period-1),volatility)

    er = change / volatility

    fast_sc = (2/(1+fast_ema))
    slow_sc = (2/(1+slow_ema))
    
    smoothing_constant = np.square(er * (fast_sc - slow_sc) + slow_sc)

    kama = simple_moving_average(data[:er_period],er_period)
    for i in range(er_period,data.shape[0]):
        new_value = kama[-1] + smoothing_constant[i]*(data[i]-kama[-1])
        kama = np.append(kama,new_value)
    
    return kama


def on_balance_volume(data:pd.DataFrame)->np.array:
    """Momentum indicator. Theory is that if volume increases without a big
    price change, a price change is coming. Implemented from:
    https://www.investopedia.com/terms/o/onbalancevolume.asp
    https://school.stockcharts.com/doku.php?id=technical_indicators:on_balance_volume_obv
    """
    closes = data["close"] - array_shift(data["close"],1)
    close_direction = np.where(closes>0,1,-1)

    # Make a mask for where OBV doesnt change
    close_direction = np.where(closes==0,0,close_direction)
    volumes = data["volume"]*close_direction

    return np.cumsum(volumes)


def bollinger_bands(data:np.array,period:int,factor:int=2):
    """Indicator used to identify whether a stock is overbought or oversold.
    Generally used in conjunciton with RSI and MACD. Use the bandwidth with 
    a long term moving average of itself to find squeezes. Implemented from:
    https://www.investopedia.com/terms/b/bollingerbands.asp
    https://school.stockcharts.com/doku.php?id=technical_indicators:bollinger_band_width
    https://school.stockcharts.com/doku.php?id=technical_indicators:bollinger_band_perce

    Parameters:
        window (int): The lags to use for our moving average
        factor (int): The number of standard deviations to account for.
    Returns upper_band,moving_average,lower_band,bandwidth,%B"""
    sma = simple_moving_average(data,period)
    views = np.lib.stride_tricks.sliding_window_view(data,period)
    standards = np.append(np.repeat(np.nan,period-1),np.std(views,axis=1))

    upper_band = sma + standards*factor
    lower_band = sma - standards*factor

    percentB = (data-lower_band)/(upper_band-lower_band)
    bandwidth = ((upper_band - lower_band) / sma) * 100

    return upper_band,sma,lower_band,bandwidth,percentB


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


def relative_strength_index(data:pd.DataFrame,period:int)->np.array:
    """Calculate Relative strength index for the data and period specified.
    Evaluates overbought and oversold conditions. Values over 70 are overbought
    and values below 30 are oversold. Implemented following:
    https://www.investopedia.com/terms/r/rsi.asp"""
    price_changes = np.diff(data["close"])

    gains = np.where(price_changes>0,price_changes,0.0)
    gains = np.insert(gains,0,0)

    losses = np.where(price_changes<0,np.abs(price_changes),0.0)
    losses = np.insert(losses,0,0)

    prev_gain = gains[:period].mean()
    prev_losses = losses[:period].mean()
    rs = np.array([*np.repeat(np.nan,period-1),prev_gain/prev_losses])

    index = period
    while index < len(data.index):
        prev_gain = (prev_gain*(period-1) + gains[index])/period
        
        prev_losses = (prev_losses*(period-1) + losses[index])/period
        prev_losses = np.where(prev_losses==0,1,prev_losses)
        
        rs = np.append(rs,prev_gain/prev_losses)
        index += 1

    return 100 - (100/(1+rs))


def stochastic_oscillator(data:pd.DataFrame,period:int)->np.array:
    """Calculates the stochastic oscillator data which is a momentum indicator
    telling us whether a stock is overbought or oversold. Overbought threshold
    is set to 80 and oversold is set at 20. Usually used with the 3 period 
    moving average of itself. Implementation follows:
    https://www.investopedia.com/terms/s/stochasticoscillator.asp"""
    
    result = np.repeat(np.nan,period-1)
    index = period
    while index < data.shape[0]+1:
        temp = data.iloc[max(0,index-period):index,:]
        high = np.max(temp["high"])
        low = np.min(temp["low"])
        close = data.iloc[index-1,:]["close"]
        result = np.append(result,((close-low)/(high-low)*100))
        index += 1
    
    return result


def ulcer_index(data:pd.DataFrame,period:int)->np.array:
    """Calculates the Ulcer index for the specified period. This is a measure
    if risk for the period. Generally when ulcer index spikes above normal 
    levels this means that a return to that price will take a long time.
    Normal levels can be ascertained from using a very long running SMA.
    Implemented from: https://www.investopedia.com/terms/u/ulcerindex.asp"""
    index = 0
    percent_drawdown_sqr = np.array([],dtype=np.float64)
    while index < data.shape[0]:
        temp = data.iloc[max(0,index-period):index,:]["close"]
        
        period_max_close = np.max(temp)
        close = data.iloc[index,:]["close"]

        drawdown = ((close - period_max_close) - period_max_close) * 100
        
        percent_drawdown_sqr = np.append(
            percent_drawdown_sqr,np.square(drawdown))
        index += 1

    index = period
    ulcer_index = np.repeat(np.nan,period-1)
    while index < data.shape[0]+1:
        temp = percent_drawdown_sqr[index-period:index]
        ulcer_index = np.append(ulcer_index,np.sqrt(np.mean(temp)))
        index += 1
    
    return ulcer_index


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
    

def balance_of_power(data:pd.DataFrame,smoothing_period:int)->np.array:
    """The Balance of power is an indicator fluctuating from -1 to 1 which 
    measures the strength of buying and selling pressure. When postive bulls
    are in charge, when negative bears. Typically smoothed using the smoothing
    period.
    
    Trends are shown by the direction the BOP is moving. So its important to 
    take a derivative of this metric. Positive will be growth.
    Implemented from:
    https://school.stockcharts.com/doku.php?id=technical_indicators:balance_of_power
    """
    bop = (data["close"]-data["open"])/(data["high"]-data["low"])
    if smoothing_period > 1:
        bop = simple_moving_average(bop,smoothing_period)
    return bop


def average_true_range(data:pd.DataFrame,period:int)->np.array:
    """Average true range is exclusively a measure of volatility. The higher
    the graph moves, the higher the volatility it is indicating. Note since
    this is an absolute measure, high price stocks will have higher ATR and
    visa versa. Reveals the degree of interest or disinterest in a move.
    Implemented from:
    https://school.stockcharts.com/doku.php?id=technical_indicators:average_true_range_atr
    
    Parameters:
        period (int): The smoothing factor for our ATR."""
    # First TR is jsut the high - the low
    temp = data.iloc[0,:]
    true_rating = np.array([temp["high"]-temp["low"]],dtype=np.float64)

    for i in range(1,len(data.index)):
        temp = data.iloc[i,:]
        prev = data.iloc[i-1,:]
        trA = temp["high"]-temp["low"]
        trB = abs(temp["high"]-prev["close"])
        trC = abs(temp["low"]-prev["close"])
        true_rating = np.append(true_rating,np.max([trA,trB,trC]))

    # First ATR is mean of first 14 periods
    atr = np.array([true_rating[:period].mean()])
    
    prev_atr = atr[-1]
    for tr in true_rating[period:]:
        atr = np.append(atr,((prev_atr*(period-1))+tr)/period)
        prev_atr = atr[-1]

    output = np.repeat(np.nan,period-1)
    return np.append(output,atr)


def money_flow_index(data:pd.DataFrame,period:int)->np.array:
    """Works similarily to RSI but incorporates volume. Values above 80 are
    considered overbought and values below 20 are oversold. It is however
    reccomended to consider 90 and 10 as the signals to avoid false signals
    due to strong pressure one way or another.
    Returns the MFI for each candle period."""
    typical_price = np.divide(data["high"]+data["low"]+data["close"],3)
    raw_money_flow = np.abs(data["volume"]*typical_price)
    
    price_diffrence = typical_price - array_shift(typical_price,1)

    positive_money = np.abs(np.where(price_diffrence>=0,raw_money_flow,0))
    negative_money = np.abs(np.where(price_diffrence<0,raw_money_flow,0))
    
    period_positive_money = np.convolve(positive_money,np.ones(period),'valid')
    period_positive_money = np.append(
        np.repeat(np.nan,period-1),period_positive_money)
    
    period_negative_money = np.convolve(negative_money,np.ones(period),'valid')
    period_negative_money = np.append(
        np.repeat(np.nan,period-1),period_negative_money)
    
    period_negative_money = np.where(
        period_negative_money==0,1,period_negative_money)

    money_flow_ratio = period_positive_money / period_negative_money
    return 100 - 100/(1 + money_flow_ratio)


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