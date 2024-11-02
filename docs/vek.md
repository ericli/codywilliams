## Issues
Need alpaca account approval
Need to pay 30$ a month for polygon data - but the data is very nice
Need to run this in parallel for multiple equities

## Enter Signal
Should be high gamma strike (ATM  + short dated)
Basic breakdown of pure momentum signal
First derivative of underlying price > 0
Ideally second derivative of underlying also > 0, but not necessary
On Balance Volume first derivative > 0
Consider RSI > 50% to indicate strong upward pressure
ADV should be >  20 … adjustable but need positive swing indication which should follow from the above
Implied Vol should be underpriced for the chosen strike, consider last traded price for the option chain structure and look for discrepancies. Possibly look at correlated assets for similarly proportioned option chain.


## Exit Signal
Best case underlying half delta gain
Any gain
Stop Loss
8% loss not worth recuperating
Problems:


## BE work to be done:

Fetch data on a minute interval and store in db:
Make a sql db to fetch from..
Fields:


Id, stock ticker, bid, ask, timestamp, volume, lastprice, *
Can have individual stock tables if speed really matters, otherwise can just do a basic query
Example query:
SELECT * from table where stock_ticker = ‘TSLA’ and ‘timestamp > ___ (some unix timestamp value’ order by desc

## chatgpt

This code connects to a SQL database to retrieve recent token data and computes key technical indicators—RSI, Stochastic RSI, and ADX—for price trends over a specified time frame. Key functions include:
query_sql: Fetches and processes token data.
enter_exit and enter_exit_stoch: Find min, max, and average values for RSI and Stochastic RSI.
get_adx: Retrieves the latest ADX value (trend strength).
get_sinusoidal: Fits a sinusoidal model to the Stochastic RSI for trend oscillations.
get_dex_and_jup_rsi: Aggregates all indicators for a given token.
The code is designed for analyzing price trends and generating trade signals.
