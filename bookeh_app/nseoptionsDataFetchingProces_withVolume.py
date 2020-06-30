import sqlite3
import pandas as pd
import time
import optionUtility as Opt_Fun
import threading
import sys
import datetime as DT
pd.set_option('display.max_rows', None)

syncTimeDelay = 6; ## in minutes time after which data will be fetched from NSE
strike_range = 12; ## in % to be selected
tableprefix = "optionChainWithVolume_"
symbol = 'NIFTY'
symbols=['NIFTY','BANKNIFTY']

databaselocation = "./niftyOptionChainAnalysis.db"



latestData = {}; # this will store the latest option chain data as a mapping of symbol
optionUtility = Opt_Fun.optionUtility(strike_range,symbols,tableprefix,databaselocation);

def continouslySaveDataFromNSEfor(symbol):
    ## Star loop ##
    table_name = tableprefix + symbol;
    print("starting thread for : " + symbol)
    con = sqlite3.connect(databaselocation)
    while True:
        try:
            #optionUtility.checkIsMarketopenAndSleepIfNot();
            df = optionUtility.getProcessedOptionChainData(symbol);
            latestData[symbol] = df;
            df.to_sql(table_name, con, if_exists='append', index=False)
            print("Synced Data for : " + symbol + " at : " + time.strftime("%c"))
            #### Delay for given minutes ####
        except Exception as e :
            print(e)
            print("Data sync failed, some error occured at time : " + time.strftime("%c"))
        if(symbol == symbols[0]):
            optionUtility.waitForGivenSecondAndUpdateConsole(syncTimeDelay * 60);
        else :
            time.sleep(syncTimeDelay * 60); # sleep the thread if it is not the first thread


        #time.sleep(syncTimeDelay * 60)
#run only for one
#continouslySaveDataFromNSEfor('BANKNIFTY')
#optionUtility.checkIsMarketopenAndSleepIfNot();
for symbol in symbols:
    ##onetimeSetup(symbol)
    t = threading.Thread(target=continouslySaveDataFromNSEfor, args=(symbol,), name = symbol)
    t.start()
#df = getProcessedOptionChainData("NIFTY");
# latestData[symbol] = df
# query = "SELECT * FROM optionChainWithVolume_NIFTY WHERE strikePrice in (9400) AND expiryDate='28-May-2020'"
# df = optionUtility.executneSQLQuery(query)
# print(df)
# #onetimeSetup("BANKNIFTY")


