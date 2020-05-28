import sqlite3
import pandas as pd
import json
import numpy as np
import requests
import time
import sys
import threading
import datetime as DT




class optionUtility :
    pd.set_option('display.max_rows', None)
     #  global variable used same across class -- have to be edited only here
    nearWeekExpiry = "28-May-2020";
    nearMonthExpirDate = "28-May-2020";
    nextMonthExpiryDate = "25-Jun-2020";
    con = sqlite3.connect(r'niftyOptionChainAnalysis.db')
    cur = con.cursor()
    # next weekl
    columnNames = "strikePrice, expiryDate, openInterest, changeinOpenInterest,impliedVolatility," \
                  " lastPrice, change, types,internalValue, externalValue,underlyingPrice,timestamp," \
                  "totalTradedVolume,totalBuyQuantity,totalSellQuantity"
    columnNames_list = ['strikePrice', 'expiryDate', 'openInterest', 'changeinOpenInterest',
                        'impliedVolatility', 'lastPrice', 'change', 'types', 'internalValue',
                        'externalValue', 'underlyingPrice', 'timestamp', 'totalTradedVolume', 'totalBuyQuantity',
                        'totalSellQuantity']  # 'totalTradedVolume','totalBuyQuantity', 'totalSellQuantity'

    ### variable coming from calling class
    # Create the connection
    #symbol = 'NIFTY'
    symbols = ['NIFTY', 'BANKNIFTY']
    tableprefix = "optionChainWithVolume_"
    strike_range = 12;  ## in % to be selected

    def __init__(self, strike_range,symbols, tablePrefix):
        self.strike_range = strike_range;
        self.symbols  =symbols
        self.tableprefix = tablePrefix;

    # query could be like 'SELECT * FROM optionChain_nifty'
    def executeSQLQuery(self,query):
        print("Executing Query : " + query);
        query = query.replace('*', self.columnNames)
        #print("Executing Query : " + query);
        self.cur.execute(query)
        df = pd.DataFrame(self.cur.fetchall(), columns=self.columnNames_list)
        return df;

    def getOptionChainDataFromNSEfor(self,symbol):
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=" + symbol
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
    def getProcessedOptionChainData(self,symbol):
        # with open('response.json') as json_file:
        #     data = json.load(json_file)
        #     allRecord = data['records']['data'];
        data = json.loads(self.getOptionChainDataFromNSEfor(symbol))
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
        lower_Range = np.floor((1-self.strike_range/100)*underlyingPrice)
        upper_Range = np.floor((1+self.strike_range/100)*underlyingPrice)

        normalize_data = pd.json_normalize(flattenedRecord)
        option_data = pd.DataFrame.from_dict(normalize_data)
        option_data = option_data.drop(columns=['identifier','underlyingValue','underlying','pchangeinOpenInterest',
                                                'pChange','bidQty','bidprice','askQty','askPrice']);
        FilteredOptionData = option_data[option_data['strikePrice']> lower_Range]
        FilteredOptionData = FilteredOptionData[option_data['strikePrice']<upper_Range]
        FilteredOptionData = FilteredOptionData[(option_data['expiryDate'] == self.nearWeekExpiry) | (option_data['expiryDate'] == self.nearMonthExpirDate)
                                 | (option_data['expiryDate'] == self.nextMonthExpiryDate)]
        FilteredOptionData['underlyingPrice'] = underlyingPrice
        FilteredOptionData['timestamp'] = DT.datetime.now().strftime("%m/%d/%Y %H:%M:%S"); #timeSync
        FilteredOptionData = FilteredOptionData[self.columnNames_list] # reorder in a given order of columns
        return FilteredOptionData.round(2);

    def checkIsMarketopenAndSleepIfNot(self):
        ### Show today's date and time ##
        now = DT.datetime.now()
        today = DT.date.today()
        tomorrow = today + DT.timedelta(days=1)
        todaycloseTime = DT.datetime.combine(today, DT.time(hour=15, minute=31))
        todayOpenTime = DT.datetime.combine(today, DT.time(hour=9, minute=16))
        nextOpeningTime = DT.datetime.combine(tomorrow, DT.time(hour=9, minute=16))
        if(now <todayOpenTime):
            nextOpeningTime = todayOpenTime;
        timeremaining = int((nextOpeningTime - now).total_seconds())
        isItFirstThread : bool= False;
        weekDay = today.weekday();
        isMarketClosed = ((now > todaycloseTime) or (now < todayOpenTime)) or (weekDay>4) ## have to do something for holidays but okay as of now.
        if(weekDay > 4 ):
            print("not a weekday");
            isMarketClosed = True;
        threadName = threading.current_thread().name;
        if((threadName == self.symbols[0] ) or (threadName == 'MainThread') ):
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

    def onetimeSetup(self,symbol):
        self.cur.execute(
            'CREATE TABLE' + self.tableprefix + symbol + '('+self.columnNames+')')

    def runatStart(self,symbol):
        self.cur.execute('SELECT * FROM '  + self.tableprefix + symbol + ';')



