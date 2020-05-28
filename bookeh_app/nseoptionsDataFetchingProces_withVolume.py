import sqlite3
import pandas as pd
import time
import optionUtility as Opt_Fun
import threading
pd.set_option('display.max_rows', None)

syncTimeDelay = 10; ## in minutes time after which data will be fetched from NSE
strike_range = 12; ## in % to be selected
tableprefix = "optionChainWithVolume_"
symbol = 'NIFTY'
symbols=['NIFTY', 'BANKNIFTY']



latestData = {}; # this will store the latest option chain data as a mapping of symbol
optionUtility = Opt_Fun.optionUtility(strike_range,symbols,tableprefix);

def continouslySaveDataFromNSEfor(symbol):
    ## Star loop ##
    table_name = tableprefix + symbol;
    print("starting thread for : " + symbol)
    con = sqlite3.connect(r'niftyOptionChainAnalysis.db')
    while True:
        try:
            optionUtility.checkIsMarketopenAndSleepIfNot();
            df = optionUtility.getProcessedOptionChainData(symbol);
            latestData[symbol] = df;
            df.to_sql(table_name, con, if_exists='append', index=False)
            print("Synced Data for : " + symbol + " at : " + time.strftime("%c"))
            #### Delay for given minutes ####
        except Exception as e :
            print(e)
            print("Data sync failed, some error occured at time : " + time.strftime("%c"))
        time.sleep(syncTimeDelay * 60)
#run only for one
continouslySaveDataFromNSEfor('BANKNIFTY')
optionUtility.checkIsMarketopenAndSleepIfNot();
for symbol in symbols:
    ##onetimeSetup(symbol)
    t = threading.Thread(target=continouslySaveDataFromNSEfor, args=(symbol,), name = symbol)
    t.start()
#df = getProcessedOptionChainData("NIFTY");
# latestData[symbol] = df

# #onetimeSetup("BANKNIFTY")


