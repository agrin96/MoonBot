from typing import Dict

def live_trade_report(state,ticker:Dict):
    """Prints some useful statistics about how we are currently doing in our
    trades."""
    # Produce a live balance that gets updated every tick.
    if state.coin_balance != 0.0:
        temp = (state.coin_balance * float(ticker["best_bid"]))*state.fee
        print(F"Appx Balance: {temp}, Coins: {state.coin_balance}")
    else:
        print(F"Current Balance: {state.current_balance},"\
              F" Coins: {state.coin_balance}")

    # Prints the baseline balance of holding long for comparison
    if state.first_price is None:
        state.first_price = float(ticker["best_ask"])
        state.initial_coin_balance =\
            (state.current_balance / state.first_price)*state.fee
    else:
        temp = (100.0 / state.first_price)*state.fee
        long = (temp * float(ticker["best_bid"]))*state.fee

        print(F"Initial Coin Balance: {state.initial_coin_balance}")
        print(F"Long Balance: {long}\n")