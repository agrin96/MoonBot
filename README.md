# MoonBot

This was an attempt at generating trees by training them on historical cryptocurrency data collected on a cheap VPS. The data was collected in csv files and then downloaded to local machine to then run a training on them to generate a tree model. The model was output to a json file an example of which is in the `SerializedTrees` directory. These files were then to be used to run autotrading through the Binance API. 

This source is the actual binance trading API, not the tree model training.

## Project Status (Dead)

Ultimately Binance pulled out of the US and so this bot was no longer useful to me as I couldn't actually use it on their platform so development work stopped. Leaving this here as a historical and educational example of what could be done.
