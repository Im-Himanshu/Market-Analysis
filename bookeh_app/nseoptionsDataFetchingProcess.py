import sqlite3
import pandas as pd
import json
import numpy as np
import requests
import time
import datetime as DT
import sys
import threading
import os

pd.set_option('display.max_rows', None)

# Create the connection
con = sqlite3.connect(r'niftyOptionChainAnalysis.db')
cur = con.cursor()
symbol = 'NIFTY'
symbols=['NIFTY', 'BANKNIFTY']

tableprefix = "optionChain_"
default_table = tableprefix+symbol
#runatStart(symbol)
strike_range = 12; ## in % to be selected
firstPID = 0;
latestData = {}; # this will store the latest option chain data as a mapping of symbol
#next weekl
nearWeekExpiry = "28-May-2020";
nearMonthExpirDate="28-May-2020";
nextMonthExpiryDate = "25-Jun-2020";
syncTimeDelay = 4; ## in minutes time after which data will be fetched from NSE


# cur.execute('CREATE TABLE optionChain_'+symbol+' (strikePrice, expiryDate, openInterest, changeinOpenInterest,impliedVolatility, lastPrice, change, types, underlyingPrice,timestamp, internalValue, externalValue)')
def onetimeSetup(symbol):
    cur.execute(
        'CREATE TABLE ' + tableprefix + symbol + ' (strikePrice, expiryDate, openInterest, changeinOpenInterest,impliedVolatility, lastPrice, change, types, underlyingPrice,timestamp, internalValue, externalValue)')


def runatStart(symbol):
    cur.execute('SELECT * FROM '  + tableprefix + symbol + ';')


# this function execute a given query and return the result in dataframe format

# query could be like 'SELECT * FROM optionChain_nifty'
def executeSQLQuery(query):
    cur.execute(query)
    df = pd.DataFrame(cur.fetchall(), columns=['strikePrice', 'expiryDate', 'openInterest', 'changeinOpenInterest',
                                               'impliedVolatility', 'lastPrice', 'change', 'types', 'underlyingPrice',
                                               'timestamp', 'internalValue', 'externalValue'])
    # for row in cur.execute('SELECT * FROM optionChain_nifty;'):
    #     print(row)
    return df;



# this function is just an helper function
# it calls th NSE website and gets the current option-chain dat for a given symbol
def getOptionChainDataFromNSEfor(symbol):
    url ="https://www.nseindia.com/api/option-chain-indices?symbol="+symbol
    header = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
      "X-Requested-With": "XMLHttpRequest"
    }
    # Pull NSE option chain
    r = requests.get(url, headers=header)
    if (r.status_code != 200):
        print("some error Occured in fetching data from NSE website Status: " + r.status_code);
        return;
    return r.content;


# Convert html page as Table and read the first table which has option data
#this function fetch data from nse website and process them to a dataframe,
# it also does useful calculation like internal value and date addition.
def getProcessedOptionChainData(symbol):
    # with open('response.json') as json_file:
    #     data = json.load(json_file)
    #     allRecord = data['records']['data'];
    data = json.loads(getOptionChainDataFromNSEfor(symbol))
    allRecord = data['records']['data'];
    allDates = data['records']['expiryDates'];
    nearestExpiryDate = allDates[0];
    flattenedRecord = []
    underlyingPrice = data['records']['underlyingValue'];
    timeSync = data['records']['timestamp']; ## time when the data was synced with the server
    for oneRecord in allRecord :
        if('CE' in oneRecord):
            oneOptionRecord = oneRecord['CE']
            oneOptionRecord['types'] = 'CE'
            flattenedRecord.append(oneOptionRecord)
            #underlyingPrice = oneOptionRecord['underlyingValue']
            oneOptionRecord['internalValue'] = np.absolute(oneOptionRecord['strikePrice'] - oneOptionRecord['underlyingValue'])
            oneOptionRecord['externalValue'] = oneOptionRecord['lastPrice'];
            if(oneOptionRecord['strikePrice'] < oneOptionRecord['underlyingValue']):
                oneOptionRecord['externalValue'] = oneOptionRecord['lastPrice']-oneOptionRecord['internalValue']
            else :
                oneOptionRecord['internalValue'] = 0;
            if (oneOptionRecord['externalValue'] < 0):
                oneOptionRecord['externalValue'] = 0

        if('PE' in oneRecord):
            oneOptionRecord = oneRecord['PE']
            oneOptionRecord['types'] = 'PE'
            flattenedRecord.append(oneOptionRecord)
            #underlyingPrice = oneOptionRecord['underlyingValue']
            oneOptionRecord['internalValue'] = np.absolute(oneOptionRecord['strikePrice'] - oneOptionRecord['underlyingValue'])
            oneOptionRecord['externalValue'] = oneOptionRecord['lastPrice'];
            if(oneOptionRecord['strikePrice'] > oneOptionRecord['underlyingValue']):
                oneOptionRecord['externalValue'] = oneOptionRecord['lastPrice']-oneOptionRecord['internalValue'];
            else :
                oneOptionRecord['internalValue'] = 0;
            if (oneOptionRecord['externalValue'] < 0):
                oneOptionRecord['externalValue'] = 0






    lower_Range = np.floor((1-strike_range/100)*underlyingPrice)
    upper_Range = np.floor((1+strike_range/100)*underlyingPrice)

    normalize_data = pd.json_normalize(flattenedRecord)
    option_data = pd.DataFrame.from_dict(normalize_data)
    option_data = option_data.drop(columns=['identifier','underlyingValue','underlying','totalTradedVolume','pchangeinOpenInterest',
                                            'pChange','totalBuyQuantity','totalSellQuantity',
                                            'bidQty','bidprice','askQty','askPrice']);
    FilteredOptionData = option_data[option_data['strikePrice']> lower_Range]
    FilteredOptionData = FilteredOptionData[option_data['strikePrice']<upper_Range]
    FilteredOptionData = FilteredOptionData[(option_data['expiryDate'] == nearWeekExpiry) | (option_data['expiryDate'] == nearMonthExpirDate)
                             | (option_data['expiryDate'] == nextMonthExpiryDate)]
    FilteredOptionData['underlyingPrice'] = underlyingPrice
    FilteredOptionData['timestamp'] = timeSync; #DT.datetime.now().strftime("%m/%d/%Y %H:%M:%S"); #timeSync
    FilteredOptionData = FilteredOptionData[['strikePrice', 'expiryDate', 'openInterest', 'changeinOpenInterest',
                               'impliedVolatility', 'lastPrice', 'change', 'types', 'underlyingPrice',
                               'timestamp', 'internalValue', 'externalValue']]

    return FilteredOptionData.round(2);

    #FilteredOptionData['internalValue'] = np.absolute(FilteredOptionData['strikePrice'] - underlyingPrice)
    # FilteredOptionData['externalValue'] = FilteredOptionData['lastPrice'];
    # df = FilteredOptionData
    # for index, row in df.iterrows():
    #     if(row['types']=='CE'):
    #         if(row['strikePrice']<underlyingPrice):
    #             row['externalValue']= row['lastPrice'] - row['internalValue']
    #     if(row['types']=='PE'):
    #         if(row['strikePrice']>underlyingPrice):
    #             row['externalValue']= row['lastPrice'] - row['internalValue']
    # FilteredOptionData['types']
    # FilteredOptionData

def checkIsMarketopen():
    ### Show today's date and time ##
    now = DT.datetime.now()
    today = DT.date.today()
    tomorrow = today + DT.timedelta(days=1)
    closeTime = DT.datetime.combine(today, DT.time(hour=15, minute=31))
    nextOpeningTime = DT.datetime.combine(tomorrow, DT.time(hour=9, minute=16))
    timeremaining = int((nextOpeningTime - now).total_seconds())
    isItFirstThread : bool= False;
    weekDay = today.weekday();
    isMarketClosed = (now > closeTime) or (weekDay>4) ## have to do something for holidays but okay as of now.
    if(weekDay > 4 ):
        print("not a weekday");
        isMarketClosed = True;
    threadName = threading.current_thread().name;
    if(threadName == symbols[0]):
        isItFirstThread = True;

    if(isMarketClosed & (not isItFirstThread)):
        print("Market is closed, sleeping till tomorrow the thread for: " +threadName)
        time.sleep(timeremaining) ## if the current thread is not the first thread sleep it till tomorrow..
    if (isMarketClosed & isItFirstThread ): # if it is a mainthread na
        #print("Market is closed as of now" + time.strftime("%c"))
        time.sleep(2) # giving time for other thread to start
        print("Monitoring time from thread for : "+ threadName)
        for remaining in range(timeremaining, 0, -1):
            time.sleep(1)
            sys.stdout.write("\r")
            timeLeft = str(DT.timedelta(seconds=remaining))
            sys.stdout.write(timeLeft + " hours remaining till market opens, time as of now : " + time.strftime("%c"))
            sys.stdout.flush()

    ## if everything goes fine, market is currently working..
def continouslySaveDataFromNSEfor(symbol):
    ## Star loop ##
    table_name = tableprefix + symbol;
    print("starting thread for : " + symbol)
    con = sqlite3.connect(r'niftyOptionChainAnalysis.db')
    while True:
        try:
            checkIsMarketopen();
            df = getProcessedOptionChainData(symbol);
            latestData[symbol] = df;
            df.to_sql(table_name, con, if_exists='append', index=False)
            print("Synced Data for : " + symbol + " at : " + time.strftime("%c"))
            #### Delay for given minutes ####
        except Exception as e :
            print(e)
            print("Data sync failed, some error occured at time : " + time.strftime("%c"))
        time.sleep(syncTimeDelay * 60)
#run only for one
#continouslySaveDataFromNSEfor('NIFTY')
checkIsMarketopen();
for symbol in symbols:
    t = threading.Thread(target=continouslySaveDataFromNSEfor, args=(symbol,), name = symbol)
    t.start()
df = getProcessedOptionChainData("NIFTY");
# latestData[symbol] = df

#onetimeSetup("BANKNIFTY")