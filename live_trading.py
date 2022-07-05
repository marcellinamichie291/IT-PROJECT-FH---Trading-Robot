# GO CHECK OUR LAST UPDATE ON GITHUB
# ----------------------------------
# https://github.com/lamachina/IT-PROJECT-FH---Trading-Robot
#
# NEW STRATEGIES COMING SOON...
# Follow the tutorial to deploy this bot


import ftx
import pandas as pd
import ta
import time
import json
from math import *

accountName = ''  # HERE YOUR SUB-ACCOUNT NAME
pairSymbol = 'BTC/USD'  # HERE THE PAIR YOU WANT TO TRADE ON FTX
fiatSymbol = 'USD'
cryptoSymbol = 'BTC'  # HERE THE SYMBOL
myTruncate = 3

# HERE YOUR API KEYS
client = ftx.FtxClient(api_key='',
                       api_secret='', subaccount_name=accountName)

data = client.get_historical_data(
    market_name=pairSymbol,
    resolution=3600,
    limit=1000,
    start_time=float(
        round(time.time()))-100*3600,
    end_time=float(round(time.time())))
df = pd.DataFrame(data)

df['EMA20'] = ta.trend.ema_indicator(df['close'], 20)
df['EMA400'] = ta.trend.ema_indicator(df['close'], 400)
df['STOCH_RSI'] = ta.momentum.stochrsi(df['close'])
# print(df)


def getBalance(myclient, coin):
    jsonBalance = myclient.get_balances()
    if jsonBalance == []:
        return 0
    pandaBalance = pd.DataFrame(jsonBalance)
    print(pandaBalance)
    if pandaBalance.loc[pandaBalance['coin'] == coin].empty:
        return 0
    else:
        return float(pandaBalance.loc[pandaBalance['coin'] == coin]['total'])


def truncate(n, decimals=0):
    r = floor(float(n)*10**decimals)/10**decimals
    return str(r)


actualPrice = df['close'].iloc[-1]
fiatAmount = getBalance(client, fiatSymbol)
cryptoAmount = getBalance(client, cryptoSymbol)
print('coin price :', actualPrice, 'usd balance',
      fiatAmount, 'coin balance :', cryptoAmount)

if float(fiatAmount) > 5 and df['EMA20'].iloc[-2] > df['EMA400'].iloc[-2] and df['STOCH_RSI'].iloc[-2] < 0.8:
    quantityBuy = truncate(float(fiatAmount)/actualPrice, myTruncate)
    buyOrder = client.place_order(
        market=pairSymbol,
        side="buy",
        price=None,
        size=quantityBuy,
        type='market')
    print(buyOrder)

elif float(cryptoAmount) > 0.001 and df['EMA20'].iloc[-2] < df['EMA400'].iloc[-2] and df['STOCH_RSI'].iloc[-2] > 0.2:
    buyOrder = client.place_order(
        market=pairSymbol,
        side="sell",
        price=None,
        size=truncate(cryptoAmount, myTruncate),
        type='market')
    print(buyOrder)
else:
    print("No opportunity to take")
