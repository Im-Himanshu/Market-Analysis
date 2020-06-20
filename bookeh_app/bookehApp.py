from bokeh.io import output_file, show
from bokeh.models import RangeSlider,Select, Panel
from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, DateRangeSlider, CheckboxButtonGroup,RadioButtonGroup


# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row, WidgetBox
import sqlite3
import numpy as np

#https://towardsdatascience.com/data-visualization-with-bokeh-in-python-part-iii-a-complete-dashboard-dc6a86aa6e23
import dashboardTools as UI_tools
import optionUtility as Opt_Fun
import threading;

class bookehApp :
    # bokeh serve --show bookeh_app
    output_file("option_dashboard.html")
    databaselocation = "../niftyOptionChainAnalysis.db"

    con = sqlite3.connect(databaselocation)
    cur = con.cursor()
    symbol = 'NIFTY'
    symbols = ['NIFTY', 'BANKNIFTY']

    tableprefix = "optionChainWithVolume_"
    default_table = tableprefix + symbol
    # runatStart(symbol)
    strike_range = 5;  ## in % to be selected
    firstPID = 0;
    isForTodayOnly = False;

    # next weekl
    syncTimeDelay = 4;  ## in minutes time after which data will be fetched from NSE

    latestData = {};  # this will store the latest option chain data as a mapping of symbol

    # new_src = dashboard_tool.make_dataset(int(9300), nearWeekExpiry, 'NIFTY', True)

    def modify_doc_dummy(self,symbol):
        print("cmoing in modify_doc_dummy")

        df = self.optionUtility.getProcessedOptionChainData(symbol);
        self.latestData[symbol] = df;
        allSources = {};

        def update(attr, old, new):
            selected_expiryDate = expiry_date_selector.value;
            # selectedStrikePrice = allUniqueStrikePrice[strikePrice_selector.active];
            activeStrikePriceIndexes = strikePrice_selector.active;  # will take top of selected if number is greater
            activeStrikePriceIndexes.sort();  # starting one will be selected
            index = 0;
            selectedStrikeNumber = activeStrikePriceIndexes.__sizeof__();
            processed = []
            # print(activeStrikePriceIndexes)
            for source in allWorkingSources:
                if (index > (selectedStrikeNumber - 1)):
                    break;  # in case less number of strike is selected don't through error
                strikeIndex = activeStrikePriceIndexes[index];
                selectedStrikePrice = allUniqueStrikePrice[strikeIndex];
                new_src = 0;
                new_src = self.dashboard_tool.make_dataset(int(selectedStrikePrice), selected_expiryDate, symbol,
                                                      self.isForTodayOnly)
                #
                # if((not (selectedStrikePrice in allSources.keys()))) :
                #     new_src = dashboard_tool.make_dataset(int(selectedStrikePrice), selected_expiryDate, symbol,
                #                                           isForTodayOnly)
                #     allSources[selectedStrikePrice]  = new_src; #save it once processed data base call is saved.. which also requires computing
                # else :
                #     new_src = allSources[selectedStrikePrice]
                source.data.update(new_src.data)
                index = index + 1;
                processed.append(selectedStrikePrice);
                # print(selectedStrikePrice) # shown prices are these..
            # print(processed, activeStrikePriceIndexes);

        allUniqueStrikePrice = self.latestData[symbol]['strikePrice'].apply(str).unique().tolist();
        ATMStrikeindex = int(np.floor(len(allUniqueStrikePrice) / 2))
        expiry_date_selector = Select(value=self.nearWeekExpiry, options=self.expiryDates)
        strikePrice_selector = CheckboxButtonGroup(labels=allUniqueStrikePrice,
                                                   active=[ATMStrikeindex - 2, ATMStrikeindex - 1, ATMStrikeindex,
                                                           ATMStrikeindex + 1,
                                                           ATMStrikeindex + 2])  # in case multiple to be shown at once#
        # strikePrice_selector = RadioButtonGroup(
        #     labels=allUniqueStrikePrice, active=ATMStrikeindex);
        #
        strikePrice_selector.on_change('active', update)
        expiry_date_selector.on_change('value', update)

        selected_expiryDate = expiry_date_selector.value;
        # selectedStrikePrice = allUniqueStrikePrice[strikePrice_selector.active];

        activeStrikePriceIndexes = strikePrice_selector.active;
        allplots = []
        allWorkingSources = []
        for oneindex in activeStrikePriceIndexes:
            selectedStrikePrice = allUniqueStrikePrice[oneindex];
            src = self.dashboard_tool.make_dataset(int(selectedStrikePrice), selected_expiryDate, symbol, self.isForTodayOnly)
            allSources[selectedStrikePrice] = src;
            allWorkingSources.append(src);
            p = self.dashboard_tool.make_plot(src, selectedStrikePrice)
            allplots.append(p);
        allplotslayout = column(allplots);
        layout = column(row(expiry_date_selector, strikePrice_selector), allplotslayout)
        tab = Panel(child=layout, title=symbol)
        return tab;

    def generateTabs(self):
        tabs = []
        for symbol in self.symbols:
            tab = self.modify_doc_dummy(symbol);
            tabs.append(tab);
        tabs = Tabs(tabs=tabs);
        return tabs;
    def __init__(self):
        print("class started")
        print("in bookeh app 126 : ", threading.current_thread());

        self.optionUtility = Opt_Fun.optionUtility(self.strike_range, self.symbols, self.tableprefix, self.databaselocation);
        self.dashboard_tool = UI_tools.UIutility(self.optionUtility, self.symbols, self.tableprefix);

        self.nearWeekExpiry = self.optionUtility.nearWeekExpiry;
        self.nearMonthExpirDate = self.optionUtility.nearMonthExpirDate;
        self.nextMonthExpiryDate = self.optionUtility.nextMonthExpiryDate;
        self.expiryDates = [self.nearWeekExpiry, self.nearMonthExpirDate, self.nextMonthExpiryDate, "All Above"]

    # curdoc().add_root(tabs);

    ## Note : it throws error when
    # 1. there is no data for the given query in the database

