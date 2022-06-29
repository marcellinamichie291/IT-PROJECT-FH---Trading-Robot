from re import X
from pyparsing import Word
from requests import request
import ftx
import pandas as pd
import json
import time
import ta
from math import *
import subprocess
import os
import telebot
from telebot import types
import pandas_ta as pda
import requests


# GET /markets
api_url = 'https://ftx.us/api'
api = '/markets'
url = api_url+api
markets = requests.get(url).json()
data = markets['result']

client = ftx.FtxClient(
    api_key='#',
    api_secret='#',
    subaccount_name='#'
)
bot = telebot.TeleBot("#")  # put ur private telegram key
id = "#"


def get_crypto(message):
    cryptoSymbol = message.text.split()[1]
    fiatSymbol = 'USD'
    pairSymbol = str(cryptoSymbol)+'/'+str(fiatSymbol)

    data = client.get_historical_data(
        market_name=pairSymbol,
        resolution=300,
        limit=1000,
        start_time=float(round(time.time()))-150*3600,
        end_time=float(round(time.time())))
    df = pd.DataFrame(data)

    actualPrice = df['close'].iloc[-1]
    return actualPrice


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(
        message.chat.id, "Hi!\nUse the following commands to get the informations you need...\n\n-----COMMANDS-----\n\n/start\nThe reception will be the ideal place if you are new. You will learn more about us… Just come!\n\n/strategy\nInforms you about our strategies.\n\n-----REQUEST-----\n\nlist COIN\nDisplay the tradings pairs we can use (think to use a good syntax.)\n\nstrategy COIN yyyy\nReturns the performance summary based on the selected strategy applied to a coin since the chosen year.\nTake care about the syntax for good result, coin must be in the list and written in CAPS\n(correct request exemple: holy_range BTC 2019\n\n")


# split le message, verifie si 'price' puis return True
def strat_request(message):
    request = message.text.split()
    print(request)
    if request[0].lower() not in "lt":
        return False
    else:
        return True


@ bot.message_handler(func=strat_request)
def send_price(message):
    cryptoSymbol = message.text.split()[1]
    start_year = message.text.split()[2]
    fiatSymbol = 'USD'
    pairSymbol = str(cryptoSymbol)+'/'+str(fiatSymbol)

    result = client.get_balances()

    data = client.get_historical_data(
        market_name=pairSymbol,
        resolution=300,
        limit=1000,
        start_time=float(round(time.time()))-150*3600,
        end_time=float(round(time.time())))
    df = pd.DataFrame(data)

    actualPrice = df['close'].iloc[-1]

    subprocess.Popen(args="python3 lt_strat.py " +
                     str(cryptoSymbol) + " " + str(start_year), shell=True,)
    # exec(open("reviewstrat.py").read())
    bot.send_message(
        message.chat.id, "Hello," + str(pairSymbol)+" price: " + str(actualPrice)+" $")
    print("ok we ready")
    docu_resume = '/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt'
    docu_trade = '/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx'
    docu_plot = '/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png'
    while True:
        checkFileExistance(docu_plot)
        print("ok " + docu_plot + " doesnt exsit")
        time.sleep(1)
        if checkFileExistance(docu_plot) == True:
            print("the file exist gg")
            break

    doc = open('/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt', 'rb')
    bot.send_document(message.chat.id, doc)
    docx = open('/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx', 'rb')
    bot.send_document(message.chat.id, docx)
    photo = open('/home/ubuntu/'+cryptoSymbol +
                 'USDT_walletVSasset.png', 'rb')
    bot.send_photo(message.chat.id, photo)
    print("files have been sent")
    time.sleep(3)
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt')
    while True:
        checkFileExistance(docu_plot)
        print(docu_plot + " still exist, wait to remove")
        time.sleep(3)
        if checkFileExistance(docu_plot) == False:
            print("file are removed")
            break


def checkFileExistance(docu_plot):
    try:
        with open(docu_plot, 'r') as f:
            return True
    except FileNotFoundError as e:
        return False
    except IOError as e:
        return False


bot.infinity_polling(skip_pending=True)
