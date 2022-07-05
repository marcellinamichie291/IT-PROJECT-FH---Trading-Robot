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
from telebot.types import Message


# GET /markets
api_url = 'https://ftx.us/api'
api = '/markets'
url = api_url+api
markets = requests.get(url).json()
data = markets['result']

# HERE YOUR FTX API KEYS
client = ftx.FtxClient(
    api_key='#',
    api_secret='#',
    subaccount_name='#'
)
# put your private telegram key
bot = telebot.TeleBot("#")
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


# Welcome
@ bot.message_handler(content_types=["new_chat_members"])
def say_welcome(message):
    bot.send_message(
        message.chat.id, "Welcome !\nClick on /help to get the informations you need :)")


# Commands guide
@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(
        message.chat.id, "-----COMMANDS-----\n\n/examples\nGive you some examples of backtesting.\n\n/infos\nExplains how to write a backtest instruction to the bot\n\n/about\nA list of useful links for the project")


# examples
@ bot.message_handler(commands=['examples'])
def choose_menu(message):
    markup = types.ReplyKeyboardMarkup()
    itembtna = types.KeyboardButton('LT BNB 2020')
    itembtnv = types.KeyboardButton('ST ETH 2022')
    itembtnc = types.KeyboardButton('LT AVAX 2020')
    markup.row(itembtna)
    markup.row(itembtnv)
    markup.row(itembtnc)
    bot.send_message(message.chat.id, "Choose one strategy:",
                     reply_markup=markup)


# Infos
@bot.message_handler(commands=['infos'])
def show_help(message):
    bot.send_message(
        message.chat.id, "To try a strategy on past data, you need 3 things:\nThe chosen strategy + the cryptocurrency to trade + the starting year.\n\nFormally follow the order of the following structure:\n(1) strategy\n(2) currency\n(3) year\n\nexamples are available in the section /examples")


# Commands guide
@bot.message_handler(commands=['about'])
def show_help(message):
    bot.send_message(
        message.chat.id, "More ressources...\n\nGitHub: https://github.com/lamachina/IT-PROJECT-FH---Trading-Robot\nTradingView: https://fr.tradingview.com/script/RZgvweBp/\n")


# split message, 'lt' return True then LT strat
def lt_request(message):
    request = message.text.split()
    print(request)
    if request[0].lower() not in "lt":
        return False
    else:
        return True


@ bot.message_handler(func=lt_request)
def send_price(message):
    cryptoSymbol = message.text.split()[1]
    start_year = message.text.split()[2]
    fiatSymbol = 'USD'
    pairSymbol = str(cryptoSymbol)+'/'+str(fiatSymbol)

    subprocess.Popen(args="python3 lt_strat.py " +
                     str(cryptoSymbol) + " " + str(start_year), shell=True,)
    bot.send_message(
        message.chat.id, "We process your request -> long term strategy on " + str(pairSymbol)+"\nThis may take a few minutes")
    print("ok we ready")
    docu_resume = '/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt'
    docu_trade = '/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx'
    docu_plot = '/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png'
    while True:
        checkFileExistance(docu_plot)
        print("ok " + docu_plot + " doesnt exsit")
        time.sleep(2)
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
    time.sleep(5)
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt')
    while True:
        checkFileExistance(docu_plot)
        print(docu_plot + " still exist, wait to remove")
        time.sleep(5)
        if checkFileExistance(docu_plot) == False:
            print("file are removed")
            break


# split message, 'lt' return True then LT strat
def st_request(message):
    request = message.text.split()
    print(request)
    if request[0].lower() not in "st":
        return False
    else:
        return True


@ bot.message_handler(func=st_request)
def send_price(message):
    cryptoSymbol = message.text.split()[1]
    start_year = message.text.split()[2]
    fiatSymbol = 'USD'
    pairSymbol = str(cryptoSymbol)+'/'+str(fiatSymbol)

    subprocess.Popen(args="python3 st_strat.py " +
                     str(cryptoSymbol) + " " + str(start_year), shell=True,)
    bot.send_message(
        message.chat.id, "We process your request -> short term strategy on " + str(pairSymbol)+"\nThis may take a few minutes")
    print("ok we ready")
    docu_resume = '/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt'
    docu_trade = '/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx'
    docu_plot = '/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png'
    while True:
        checkFileExistance(docu_plot)
        print("ok " + docu_plot + " doesnt exsit")
        time.sleep(2)
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
    time.sleep(5)
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_walletVSasset.png')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_AllTrades.xlsx')
    os.unlink('/home/ubuntu/'+cryptoSymbol+'USDT_resume.txt')
    while True:
        checkFileExistance(docu_plot)
        print(docu_plot + " still exist, wait to remove")
        time.sleep(5)
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
