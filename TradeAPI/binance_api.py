import api_requests as api
from typing import Optional

BASE_URL = "https://api.binance.com"

class RequestType:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

#------------------------------------------------------------------------#
# Public API functions. Dont require secret.
#------------------------------------------------------------------------#

def server_ping():
    """Ping the Binance API endpoint to test connectivity"""
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/ping")


def server_time():
    """Get the current server time of the binance exchange."""
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/time")


def exchange_information():
    """Get information about current rules in the binance exchange."""
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/exchangeInfo")


def order_book(symbol:str,limit:int):
    """
    Get information about the order book. This gives you a list of the current
    bids and asks with their price and quantity specified. The API limit is 5k.
    In the response lists, the values are [price,qty]

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        limit (int): The number of orders to retrieve. 5,10,100,500,1000,5000
    """
    params = F"symbol={symbol}&limit={limit}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/depth",
        request_params=params)


def recent_trades(symbol:str,limit:int):
    """
    Information about recent trades for the market specified.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        limit (int): The number of trades to retrieve. 1-1000
    """
    params = F"symbol={symbol}&limit={limit}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/trades",
        request_params=params)


def daily_price_ticker_stats(symbol:str):
    """
    The 24 hour rolling window price movement statistics.
    Weight = 1 | 40 for all

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
    """
    params = F"symbol={symbol}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/ticker/24hr",
        request_params=params)


def latest_ticker_price(symbol:str):
    """
    Get the latest bid price on the order book for the specified ticker.
    Weight = 1 | 2 for all

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
    """
    params = F"symbol={symbol}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/ticker/price",
        request_params=params)


def best_ticker_price(symbol:str):
    """
    Get the best price and qty on the order book for a symbol. This is both
    the bid and the ask price.
    Weight = 1 | 2 for all

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
    """
    params = F"symbol={symbol}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/ticker/bookTicker",
        request_params=params)


#------------------------------------------------------------------------#
# Private API functions. Require SHA256 hash
#------------------------------------------------------------------------#

class Side:
    """Determines whether you are buying or selling the first of a symbol pair"""
    SELL = "SELL"
    BUY = "BUY"

class OrderType:
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"

class TimeInForce:
    """Good until cancelled. Waits however long it takes to fulfill."""
    GTC = "GTC"
    """
    Fill or kill tries to execute the order all at once. 
    If it can't its cancelled."""
    FOK = "FOK"
    """
    Immediate or cancel. All or part of the 
    order must be completed or its cancelled."""
    IOC = "IOC"

class OrderResponseType:
    """Determines how detailed the response is when placing orders."""
    ACK = "ACK"
    RESULT = "RESULT"
    FULL = "FULL"


def place_order(
        symbol:str,
        side:Side,
        type:OrderType,
        quantity:str,
        price:str,
        timing:TimeInForce,
        stop_price:Optional[str]=None,
        order_response:Optional[OrderResponseType]=None,
        is_test:bool=False):
    """
    Order submission function.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        side (Side): The type of order. Buy or Sell BTC
        type (OrderType): The order category LIMIT/MARKET etc.
        quantity (str): A string with predefined decimal place accuracy.
        price (str): A price string with the set number of decimal places.
        timing (TimeInForce): The completion timing type of this order.
        stop_price (str): The optional stop price of the order.
        order_response (Optional[OrderResponseType]): The detail level of the response.
        is_test (bool): Whether this order should be sent as a test.
    """
    params = F"symbol={symbol}"\
        F"&side={side}"\
        F"&type={type}"\
        F"&quantity={quantity}"\
        F"&timeInForce={timing}"\
        F"&price={price}"
    if stop_price:
        params += F"&stopPrice={stop_price}"
    if order_response:
        params += F"&newOrderRespType={order_response}"

    url = F"{BASE_URL}/api/v3/order"
    if is_test:
        url = F"{BASE_URL}/api/v3/order/test"

    return api.send_request(
        method=RequestType.POST,
        request_url=url,
        request_params=params,
        is_public=False)


def market_buy(symbol:str,
               quote_quantity:str,
               order_response:Optional[OrderResponseType]=None,
               is_test:bool=False):
    """Execute a Market buy at the quote order quantity. This means that for
    BTCUSDT we are buying based on USDT. So if we have 100 USDT, we will buy
    as much BTC as 100 USDT allows. We are buyin at the current market rate
    whatever it is so price is irrelavent as a field.
    """
    params = F"symbol={symbol}"\
             F"&side={Side.BUY}"\
             F"&type={OrderType.MARKET}"\
             F"&quoteOrderQty={quote_quantity}"
    if order_response:
        params += F"&newOrderRespType={order_response}"

    url = F"{BASE_URL}/api/v3/order"
    if is_test:
        url = F"{BASE_URL}/api/v3/order/test"

    return api.send_request(
        method=RequestType.POST,
        request_url=url,
        request_params=params,
        is_public=False)


def market_sell(symbol:str,
               base_quantity:str,
               order_response:Optional[OrderResponseType]=None,
               is_test:bool=False):
    """Execute a Market sell at the base order quantity. This means that for
    BTCUSDT we are selling based on BTC. So if we have 0.15 BTC, we will sell
    for the max amount of USDT that BTC can get us. We are buyin at the current 
    market rate whatever it is so price is irrelavent as a field.
    """
    params = F"symbol={symbol}"\
             F"&side={Side.SELL}"\
             F"&type={OrderType.MARKET}"\
             F"&quantity={base_quantity}"
    if order_response:
        params += F"&newOrderRespType={order_response}"

    url = F"{BASE_URL}/api/v3/order"
    if is_test:
        url = F"{BASE_URL}/api/v3/order/test"

    return api.send_request(
        method=RequestType.POST,
        request_url=url,
        request_params=params,
        is_public=False)


def limit_buy(
        symbol:str,
        quantity:str,
        price:str,
        timing:TimeInForce,
        order_response:Optional[OrderResponseType] = None):
    """
    LIMIT Buy order submission function.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        quantity (str): A string with predefined decimal place accuracy.
        price (str): A price string with the set number of decimal places.
        timing (TimeInForce): The completion timing type of this order.
        order_response (Optional[OrderResponseType]): The detail level of the response.
    """
    return place_order(
        symbol=symbol,
        side=Side.BUY,
        type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timing=timing,
        order_response=order_response)


def stop_limit_buy(
        symbol:str,
        quantity:str,
        price:str,
        timing:TimeInForce,
        stop_price:str,
        order_response:Optional[OrderResponseType] = None):
    """
    A stop limit buy order uses two prices. The stop price determines the trigger
    at which point the limit order is placed. The regular price will be the
    actual limit order price. For a buy it is reccomended to set the trigger
    a little lower than the limit price. This guarantees it fulfills. If the trigger 
    is 10$ and the limit is 11$ then your order is likely to get instantly filled.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        quantity (str): A string with predefined decimal place accuracy.
        price (str): A price string with the set number of decimal places.
        timing (TimeInForce): The completion timing type of this order.
        stop_price (str): The trigger price at which to set the order.
        order_response (Optional[OrderResponseType]): The detail level of the response.
    """
    return place_order(
        symbol=symbol,
        side=Side.BUY,
        type=OrderType.STOP_LOSS_LIMIT,
        stop_price=stop_price,
        quantity=quantity,
        price=price,
        timing=timing,
        order_response=order_response)


def stop_limit_sell(
        symbol:str,
        quantity:str,
        price:str,
        timing:TimeInForce,
        stop_price:str,
        order_response:Optional[OrderResponseType] = None):
    """
    A stop limit sell order (take profit) uses two prices. The stop price determines 
    the trigger at which point the limit order is placed. The regular price will be the
    actual limit order price. For a sell it is reccomended to set the trigger
    a little higher than the limit price. This guarantees it fulfills. If the trigger 
    is 11$ and the limit is 10$ then your order is likely to get instantly filled.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        quantity (str): A string with predefined decimal place accuracy.
        price (str): A price string with the set number of decimal places.
        timing (TimeInForce): The completion timing type of this order.
        stop_price (str): The trigger price at which to set the order.
        order_response (Optional[OrderResponseType]): The detail level of the response.
    """
    return place_order(
        symbol=symbol,
        side=Side.SELL,
        type=OrderType.TAKE_PROFIT_LIMIT,
        stop_price=stop_price,
        quantity=quantity,
        price=price,
        timing=timing,
        order_response=order_response)


def limit_sell(
        symbol:str,
        quantity:str,
        price:str,
        timing:TimeInForce,
        order_response:Optional[OrderResponseType] = None):
    """
    LIMIT Sell order submission function.

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        quantity (str): A string with predefined decimal place accuracy.
        price (str): A price string with the set number of decimal places.
        timing (TimeInForce): The completion timing type of this order.
        order_response (Optional[OrderResponseType]): The detail level of the response.
    """
    return place_order(
        symbol=symbol,
        side=Side.SELL,
        type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timing=timing,
        order_response=order_response)


def all_account_orders(
        symbol:str,
        limit:int,
        order_id:Optional[int]=None,
        start_time:Optional[int]=None,
        end_time:Optional[int]=None):
    """
    Get all orders from this account. This includes completed and cancelled.
    Weight = 1

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        limit (int): The number of orders to return. Max 1000.
        order_id (Optional[int]): An order id to start from and return.
        start_time (Optional[int]): Optionally return from a certain time.
        end_time (Optional[int]): Optionally time to return up to.
    """
    params = F"symbol={symbol}&limit={limit}"
    if order_id:
        params = F"{params}&orderId={order_id}"
    if start_time:
        params = F"{params}&startTime={start_time}"
    if start_time < end_time:
        params = F"{params}&endTime={end_time}"

    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/allOrders",
        request_params=params,
        is_public=False)


def current_open_orders(symbol:str):
    """
    Get all open orders from this account. This includes completed and cancelled.
    Weight = 1 | 40 for all symbols

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
    """
    params = F"symbol={symbol}"

    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/openOrders",
        request_params=params,
        is_public=False)


def cancel_order(symbol:str,order_id:int):
    """
    Cancel an open order based on its ID.
    Weight = 1 | 40 for all symbols

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        order_id (int): The unique id generated by the order.
    """
    params = F"symbol={symbol}&orderId={order_id}"
    return api.send_request(
        method=RequestType.DELETE,
        request_url=F"{BASE_URL}/api/v3/order",
        request_params=params,
        is_public=False)


def order_status(symbol:str,order_id:int):
    """
    Get the order status based on this order id.
    Weight = 1 | 40 for all symbols

    Parameters:
        symbol (str): The market symbol ticker pair such as BTCUSDT.
        order_id (int): The unique id generated by the order.
    """
    params = F"symbol={symbol}&orderId={order_id}"
    return api.send_request(
        method=RequestType.GET,
        request_url=F"{BASE_URL}/api/v3/order",
        request_params=params,
        is_public=False)


def account_information(hide_small_balances:bool=True,
                        only_balances:bool=False,
                        symbol:str=None):
    """
    Get current account information for this user.
    Weight = 5
    """
    res = api.send_request(method=RequestType.GET,
                           request_url=F"{BASE_URL}/api/v3/account",
                           is_public=False)
    if "data" not in res:
        raise RuntimeError(F"Error on dat aread: {res}")
    res = res["data"]
    
    if symbol:
        for b in res["balances"]:
            if b["asset"] == symbol:
                return b
        raise RuntimeError(F"Failed to find asset: {b}")

    if "balances" in res:
        output = []
        if hide_small_balances:
            for b in res["balances"]:
                if float(b["free"]) + float(b["locked"]) > 1e-8:
                    output.append(b)
        else:
            output = res["balances"]
        res["balances"] = output

    if only_balances:
        return res["balances"]
    else:
        return res
        


if __name__ == "__main__":
    # print(server_ping())
    # print(server_time())
    # print(exchange_information()["symbols"])
    # print(market_orderbook(symbol="BTCUSDT",limit=5))
    # print(len(recent_trades(symbol="BTCUSDT",limit=1000)["data"]))
    # print(daily_price_ticker_stats(symbol="BTCUSDT"))
    # print(latest_ticker_price(symbol="BTCUSDT"))
    # print(best_ticker_price_quantity(symbol="BTCUSDT"))
    # res = all_account_orders(
    #     symbol="BTCUSDT",
    #     limit=1)
    # print(res)
    res = account_information(symbol="BTC")
    print(res)

    # res = market_buy(symbol="BTCUSDT",quote_quantity=100,is_test=True)
    # print(res)
    # res = market_sell(symbol="BTCUSDT",base_quantity=0.15,is_test=True)
    # print(res)