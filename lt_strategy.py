import pandas as pd
from binance.client import Client
import ta
import numpy as np
import pandas_ta as pda

import matplotlib.pyplot as plt
import os
import sys

print(sys.argv[0])
print(sys.argv[1])
print(sys.argv[2])

client = Client()
pair_symbol = str(sys.argv[1])+"USDT"
time_interval = Client.KLINE_INTERVAL_1HOUR
start_date = "01 january " + str(sys.argv[2])

klinesT = client.get_historical_klines(pair_symbol, time_interval, start_date)
df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close',
                  'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
df.drop(columns=df.columns.difference(
    ['timestamp', 'open', 'high', 'low', 'close', 'volume']), inplace=True)
for col in df.columns:
    df[col] = pd.to_numeric(df[col])
df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']
df.drop(columns=df.columns.difference(
    ['timestamp', 'open', 'high', 'low', 'close', 'volume']), inplace=True)
# Heiki Ashi Bar


def heikinashi_df(df):
    df['ha_close'] = (df.open + df.high + df.low + df.close)/4
    ha_open = [(df.open[0] + df.close[0]) / 2]
    [ha_open.append((ha_open[i] + df.ha_close.values[i]) / 2)
     for i in range(0, len(df)-1)]
    df['ha_open'] = ha_open
    df['ha_high'] = df[['ha_open', 'ha_close', 'high']].max(axis=1)
    df['ha_low'] = df[['ha_open', 'ha_close', 'low']].min(axis=1)
    return df


df = heikinashi_df(df)

#---------------------------- #
df.drop(columns=df.columns.difference(
    ['timestamp', 'open', 'high', 'low', 'close', 'volume']), inplace=True)

# EMA
df['ema7'] = ta.trend.ema_indicator(close=df['close'], window=7)
df['ema11'] = ta.trend.ema_indicator(close=df['close'], window=11)
df['ema20'] = ta.trend.ema_indicator(close=df['close'], window=20)
df['ema30'] = ta.trend.ema_indicator(close=df['close'], window=30)
df['ema50'] = ta.trend.ema_indicator(close=df['close'], window=50)
df['ema100'] = ta.trend.ema_indicator(close=df['close'], window=100)
df['ema150'] = ta.trend.ema_indicator(close=df['close'], window=150)
df['ema200'] = ta.trend.ema_indicator(close=df['close'], window=200)
df['ema400'] = ta.trend.ema_indicator(close=df['close'], window=400)
#------------------------- #

# SMA
df['sma7'] = ta.trend.sma_indicator(close=df['close'], window=7)
#---------------------------- #


# Supertrend
class SuperTrend():
    def __init__(
        self,
        high,
        low,
        close,
        atr_window=15,
        atr_multi=6
    ):
        self.high = high
        self.low = low
        self.close = close
        self.atr_window = atr_window
        self.atr_multi = atr_multi
        self._run()

    def _run(self):
        # calculate ATR
        price_diffs = [self.high - self.low,
                       self.high - self.close.shift(),
                       self.close.shift() - self.low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        # default ATR calculation in supertrend indicator
        atr = true_range.ewm(alpha=1/self.atr_window,
                             min_periods=self.atr_window).mean()
        # atr = ta.volatility.average_true_range(high, low, close, atr_period)
        # df['atr'] = df['tr'].rolling(atr_period).mean()

        # HL2 is simply the average of high and low prices
        hl2 = (self.high + self.low) / 2
        # upperband and lowerband calculation
        # notice that final bands are set to be equal to the respective bands
        final_upperband = upperband = hl2 + (self.atr_multi * atr)
        final_lowerband = lowerband = hl2 - (self.atr_multi * atr)

        # initialize Supertrend column to True
        supertrend = [True] * len(self.close)

        for i in range(1, len(self.close)):
            curr, prev = i, i-1

            # if current close price crosses above upperband
            if self.close[curr] > final_upperband[prev]:
                supertrend[curr] = True
            # if current close price crosses below lowerband
            elif self.close[curr] < final_lowerband[prev]:
                supertrend[curr] = False
            # else, the trend continues
            else:
                supertrend[curr] = supertrend[prev]

                # adjustment to the final bands
                if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                    final_lowerband[curr] = final_lowerband[prev]
                if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                    final_upperband[curr] = final_upperband[prev]

            # to remove bands according to the trend direction
            if supertrend[curr] == True:
                final_upperband[curr] = np.nan
            else:
                final_lowerband[curr] = np.nan

        self.st = pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        })

    def super_trend_upper(self):
        return self.st['Final Upperband']

    def super_trend_lower(self):
        return self.st['Final Lowerband']

    def super_trend_direction(self):
        return self.st['Supertrend']


st_atr_window = 15
st_atr_multiplier = 6

super_trend = SuperTrend(df['high'], df['low'],
                         df['close'], st_atr_window, st_atr_multiplier)
df['super_trend_direction'] = super_trend.super_trend_direction()
df['super_trend_upper'] = super_trend.super_trend_upper()
df['super_trend_lower'] = super_trend.super_trend_lower()
#---------------------------- #


# TRIX
class Trix():
    """ Trix indicator

        Args:
            close(pd.Series): dataframe 'close' columns,
            trixLength(int): the window length for each mooving average of the trix,
            trixSignal(int): the window length for the signal line
    """

    def __init__(
        self,
        close: pd.Series,
        trixLength: int = 9,
        trixSignal: int = 21
    ):
        self.close = close
        self.trixLength = trixLength
        self.trixSignal = trixSignal
        self._run()

    def _run(self):
        self.trixLine = ta.trend.ema_indicator(
            ta.trend.ema_indicator(
                ta.trend.ema_indicator(
                    close=self.close, window=self.trixLength),
                window=self.trixLength), window=self.trixLength)
        self.trixPctLine = self.trixLine.pct_change()*100
        self.trixSignalLine = ta.trend.sma_indicator(
            close=self.trixPctLine, window=self.trixSignal)
        self.trixHisto = self.trixPctLine - self.trixSignalLine

    def trix_line(self) -> pd.Series:
        """ trix line

            Returns:
                pd.Series: trix line
        """
        return pd.Series(self.trixLine, name="TRIX_LINE")

    def trix_pct_line(self) -> pd.Series:
        """ trix percentage line

            Returns:
                pd.Series: trix percentage line
        """
        return pd.Series(self.trixPctLine, name="TRIX_PCT_LINE")

    def trix_signal_line(self) -> pd.Series:
        """ trix signal line

            Returns:
                pd.Series: trix siganl line
        """
        return pd.Series(self.trixSignal, name="TRIX_SIGNAL_LINE")

    def trix_histo(self) -> pd.Series:
        """ trix histogram

            Returns:
                pd.Series: trix histogram
        """
        return pd.Series(self.trixHisto, name="TRIX_HISTO")


trix_length = 9
trix_signal = 21
trix = Trix(df["close"], trix_length, trix_signal)
df['trix_pct_line'] = trix.trix_pct_line()
df['trix_signal_line'] = trix.trix_signal_line()
df['trix_histo'] = trix.trix_histo()

#------------------------ #


# MACD
macd = ta.trend.MACD(
    close=df['close'], window_fast=12, window_slow=26, window_sign=9)
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_histo'] = macd.macd_diff()
#----------------------- #
dfTest = df.copy()
initial_wallet = 1000
taker_fee = 0.0007

sl_price = 0
tp_price = 1000000

wallet = initial_wallet
usd = initial_wallet
coin = 0

trades_hitory = []
days_history = []
previous_day = 0
buy_ready = True

previous_row = df.iloc[0].copy()


def buy_condition(row, previous_row=None):
    readytobuy = False
    if row['ema20'] > row['ema400'] and row['super_trend_direction'] == True:
        readytobuy = True
        if readytobuy == True and previous_row['close'] > previous_row['ema20'] and row['close'] < row['ema20']:
            return True
    else:
        return False


def sell_condition(row, previous_row=None):

    if row['ema20'] < row['ema400'] and previous_row['close'] < previous_row['ema20'] and row['close'] > row['ema20']:
        return True
    else:
        return False


for index, row in df.iterrows():

    current_day = index.day
    if previous_day != current_day:
        temp_wallet = wallet
        if coin > 0:
            temp_wallet = coin*row['close']
        days_history.append({
            "day": str(index.year)+"-"+str(index.month)+"-"+str(index.day),
            "wallet": temp_wallet,
            "price": row['close']
        })
    previous_day = current_day

    if buy_condition(row, previous_row) == True and usd > 0 and buy_ready == True:
        coin = usd / row['close']
        fee = taker_fee * coin
        coin = coin - fee
        usd = 0
        wallet = coin * row['close']
        buy_data = {
            'date': index,
            'position': 'buy',
            'price': row['close'],
            'fee': fee * row['close'],
            'usd': usd,
            'coin': coin,
            'wallet': wallet,
            'reason': "market"
        }
        trades_hitory.append(buy_data)
        sl_price = row['close']*0.88

    elif row['low'] < sl_price and coin > 0:
        usd = coin * sl_price
        fee = taker_fee * usd
        usd = usd - fee
        coin = 0
        wallet = usd
        sell_data = {
            'date': index,
            'position': 'sell',
            'price': sl_price,
            'fee': fee,
            'usd': usd,
            'coin': coin,
            'wallet': wallet,
            'reason': "stop loss"
        }
        trades_hitory.append(sell_data)

    elif row['high'] > tp_price and coin > 0:
        usd = coin * tp_price
        fee = taker_fee * usd
        usd = usd - fee
        coin = 0
        wallet = usd
        sell_data = {
            'date': index,
            'position': 'sell',
            'price': tp_price,
            'fee': fee,
            'usd': usd,
            'coin': coin,
            'wallet': wallet,
            'reason': "take profit"

        }
        trades_hitory.append(sell_data)

    elif sell_condition(row, previous_row) == True:
        buy_ready = True
        if coin > 0:
            usd = coin * row['close']
            fee = taker_fee * usd
            usd = usd - fee
            coin = 0
            wallet = usd
            sell_data = {
                'date': index,
                'position': 'sell',
                'price': row['close'],
                'fee': fee,
                'usd': usd,
                'coin': coin,
                'wallet': wallet,
                'reason': "market"
            }
            trades_hitory.append(sell_data)

    previous_row = row

df_days = pd.DataFrame(days_history)
df_days['day'] = pd.to_datetime(df_days['day'])
df_days = df_days.set_index(df_days['day'])

df_trades = pd.DataFrame(trades_hitory)
df_trades['date'] = pd.to_datetime(df_trades['date'])
df_trades = df_trades.set_index(df_trades['date'])


def plot_bar_by_month(df_days):
    sns.set(rc={'figure.figsize': (11.7, 8.27)})
    custom_palette = {}

    last_month = int(df_days.iloc[-1]['day'].month)
    last_year = int(df_days.iloc[-1]['day'].year)

    current_month = int(df_days.iloc[0]['day'].month)
    current_year = int(df_days.iloc[0]['day'].year)
    current_year_array = []
    while current_year != last_year or current_month-1 != last_month:
        date_string = str(current_year) + "-" + str(current_month)

        monthly_perf = (df_days.loc[date_string]['wallet'].iloc[-1] - df_days.loc[date_string]
                        ['wallet'].iloc[0]) / df_days.loc[date_string]['wallet'].iloc[0]
        monthly_row = {
            'date': str(datetime.date(1900, current_month, 1).strftime('%B')),
            'result': round(monthly_perf*100)
        }
        if monthly_row["result"] >= 0:
            custom_palette[str(datetime.date(
                1900, current_month, 1).strftime('%B'))] = 'g'
        else:
            custom_palette[str(datetime.date(
                1900, current_month, 1).strftime('%B'))] = 'r'
        current_year_array.append(monthly_row)
        if ((current_month == 12) or (current_month == last_month and current_year == last_year)):
            current_df = pd.DataFrame(current_year_array)
            g = sns.barplot(data=current_df, x='date',
                            y='result', palette=custom_palette)
            for index, row in current_df.iterrows():
                if row.result >= 0:
                    g.text(row.name, row.result, '+'+str(round(row.result)
                                                         )+'%', color='black', ha="center", va="bottom")
                else:
                    g.text(row.name, row.result, '-'+str(round(row.result)
                                                         )+'%', color='black', ha="center", va="top")
            g.set_title(str(current_year) + ' performance in %')
            g.set(xlabel=current_year, ylabel='performance %')

            year_result = (df_days.loc[str(current_year)]['wallet'].iloc[-1] - df_days.loc[str(
                current_year)]['wallet'].iloc[0]) / df_days.loc[str(current_year)]['wallet'].iloc[0]
            print("----- " + str(current_year) + " Cumulative Performances: " +
                  str(round(year_result*100, 2)) + "% -----")
            plt.show()

            current_year_array = []

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1


def plot_wallet_vs_asset(df_days):
    fig, axes = plt.subplots(figsize=(15, 12), nrows=2, ncols=1)
    df_days['wallet'].plot(ax=axes[0])
    df_days['price'].plot(ax=axes[1], color='orange')


def show_analys(days, trades):
    df_trades = trades.copy()
    df_days = days.copy()

    df_days['evolution'] = df_days['wallet'].diff()
    df_trades['trade_result'] = df_trades['wallet'].diff()
    df_trades['trade_result_pct'] = df_trades['wallet'].pct_change()

    df_days['wallet_ath'] = df_days['wallet'].cummax()
    df_days['drawdown'] = df_days['wallet_ath'] - df_days['wallet']
    df_days['drawdown_pct'] = df_days['drawdown'] / df_days['wallet_ath']

    initial_wallet = df_days.iloc[0]["wallet"]

    close_trades = df_trades.loc[df_trades['position'] == 'sell']
    good_trades = close_trades.loc[close_trades['trade_result_pct'] > 0]
    total_trades = len(close_trades)
    total_good_trades = len(good_trades)
    avg_profit = close_trades['trade_result_pct'].mean()
    global_win_rate = total_good_trades / total_trades
    max_days_drawdown = df_days['drawdown_pct'].max()
    final_wallet = df_days.iloc[-1]['wallet']
    buy_and_hold_pct = (
        df_days.iloc[-1]['price'] - df_days.iloc[0]['price']) / df_days.iloc[0]['price']
    buy_and_hold_wallet = initial_wallet + initial_wallet * buy_and_hold_pct
    vs_hold_pct = (final_wallet - buy_and_hold_wallet)/buy_and_hold_wallet
    vs_usd_pct = (final_wallet - initial_wallet)/initial_wallet
    total_fee = df_trades['fee'].sum()

    best_trade = df_trades['trade_result_pct'].max()
    best_trade_date = str(
        df_trades.loc[df_trades['trade_result_pct'] == best_trade].iloc[0]['date'])
    worst_trade = df_trades['trade_result_pct'].min()
    worst_trade_date = str(
        df_trades.loc[df_trades['trade_result_pct'] == worst_trade].iloc[0]['date'])

    print("Period: [{}] -> [{}]".format(df_days.iloc[0]
          ["day"], df_days.iloc[-1]["day"]))
    print("Initial wallet: {} $".format(round(initial_wallet, 2)))

    print("\n--- General Information ---")
    print("Final wallet: {} $".format(round(final_wallet, 2)))
    print("Performance vs US dollar: {} %".format(round(vs_usd_pct*100, 2)))
    print("Worst Drawdown : -{}%".format(round(max_days_drawdown*100, 2)))
    print("Buy and hold performance: {} %".format(
        round(buy_and_hold_pct*100, 2)))
    print("Performance vs buy and hold: {} %".format(round(vs_hold_pct*100, 2)))
    print("Total trades on the period: {}".format(total_trades))
    print("Global Win rate: {} %".format(round(global_win_rate*100, 2)))
    print("Average Profit: {} %".format(round(avg_profit*100, 2)))
    print("Total fee: {} $".format(round(total_fee, 2)))

    print("\nBest trades: +{} % the {}".format(round(best_trade*100, 2), best_trade_date))
    print("Worst trades: {} % the {}".format(
        round(worst_trade*100, 2), worst_trade_date))

    save_path = "/home/ubuntu/"
    fichier = open(save_path+pair_symbol+'_resume.txt', "w")
    fichier.write("Period: [{}] -> [{}]".format(df_days.iloc[0]
                                                ["day"], df_days.iloc[-1]["day"]))
    fichier.write("\n\n--- Strategy ---")
    fichier.write("\n\n--- General Information ---")
    fichier.write("\nInitial wallet: {} $".format(round(initial_wallet, 2)))
    fichier.write("\nFinal wallet: {} $".format(round(final_wallet, 2)))
    fichier.write("\n\nPerformance vs US dollar: {} %".format(
        round(vs_usd_pct*100, 2)))
    fichier.write("\nPerformance vs buy and hold: {} %".format(
        round(vs_hold_pct*100, 2)))
    fichier.write("\nBuy and hold performance: {} %".format(
        round(buy_and_hold_pct*100, 2)))
    fichier.write(
        "\n\nWorst Drawdown : -{}%".format(round(max_days_drawdown*100, 2)))
    fichier.write("\nTotal trades on the period: {}".format(total_trades))
    fichier.write("\nGlobal Win rate: {} %".format(
        round(global_win_rate*100, 2)))
    fichier.write("\nAverage Profit: {} %".format(round(avg_profit*100, 2)))
    fichier.write("\nTotal fee: {} $".format(round(total_fee, 2)))
    fichier.write(
        "\n\nBest trades: +{} % the {}".format(round(best_trade*100, 2), best_trade_date))
    fichier.write("\nWorst trades: {} % the {}".format(
        round(worst_trade*100, 2), worst_trade_date))


show_analys(df_days.loc[:], df_trades.loc[:])

print("\n--- Plot wallet evolution vs asset ---")
plot_wallet_vs_asset(df_days.loc[:])

df_trades

save_path = "/home/ubuntu/"

plt.savefig(save_path + pair_symbol +
            '_walletVSasset.png', bbox_inches='tight')

completeName = os.path.join(save_path, pair_symbol+".txt")

df_trades.to_csv(save_path + pair_symbol + '_AllTrades.csv')

read_file = pd.read_csv(save_path + pair_symbol +
                        '_AllTrades.csv')

excelWriter = pd.ExcelWriter(
    save_path + pair_symbol + '_AllTrades.xlsx')

read_file.to_excel(excelWriter)

excelWriter.save()

os.remove(save_path + pair_symbol + '_AllTrades.csv')
