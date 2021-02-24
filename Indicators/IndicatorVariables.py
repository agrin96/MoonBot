from .Indicators import (
    BalanceOfPower,
    ChaikinOscillator,
    MovingAverageConverganceDivergence,
    MoneyFlowIndex,
    RelativeStrengthIndex)

indicator_variables = [
    {
        "name": "bop",
        "generator": BalanceOfPower,
    },
    {
        "name": "rsi",
        "generator": RelativeStrengthIndex
    },
    {
        "name": "chaikin",
        "generator": ChaikinOscillator,
    },
    {
        "name": "mfi",
        "generator": MoneyFlowIndex,
    },
    {
        "name": "macd",
        "generator": MovingAverageConverganceDivergence,
    },
]