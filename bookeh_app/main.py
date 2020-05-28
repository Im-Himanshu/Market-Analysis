from bokeh.io import output_file, show
from bokeh.models import RangeSlider,Select
from bokeh.io import show, output_notebook, push_notebook
from bokeh.plotting import figure

from bokeh.models import CategoricalColorMapper, HoverTool, ColumnDataSource, Panel
from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, DateRangeSlider, CheckboxButtonGroup,RadioButtonGroup


# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row, WidgetBox
#from bokeh.palettes import Category20_16
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

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application

#https://towardsdatascience.com/data-visualization-with-bokeh-in-python-part-iii-a-complete-dashboard-dc6a86aa6e23
import dashboardTools as UI_tools
import optionUtility as Opt_Fun
#bokeh serve --show bokeh_app
output_file("option_dashboard.html")

con = sqlite3.connect('niftyOptionChainAnalysis.db')
cur = con.cursor()
symbol = 'NIFTY'
symbols=['NIFTY', 'BANKNIFTY']

tableprefix = "optionChainWithVolume_"
default_table = tableprefix+symbol
#runatStart(symbol)
strike_range = 5; ## in % to be selected
firstPID = 0;
isForTodayOnly = True;


#next weekl
syncTimeDelay = 4; ## in minutes time after which data will be fetched from NSE

latestData = {}; # this will store the latest option chain data as a mapping of symbol


optionUtility = Opt_Fun.optionUtility(strike_range,symbols,tableprefix);
dashboard_tool = UI_tools.UIutility(optionUtility,symbols,tableprefix);


nearWeekExpiry = optionUtility.nearWeekExpiry;
nearMonthExpirDate=optionUtility.nearMonthExpirDate;
nextMonthExpiryDate = optionUtility.nearMonthExpirDate;

expiryDates = [nearWeekExpiry,nearMonthExpirDate,nextMonthExpiryDate, "All Above"]

#new_src = dashboard_tool.make_dataset(int(9300), nearWeekExpiry, 'NIFTY', True)

def modify_doc():

    df = optionUtility.getProcessedOptionChainData("NIFTY");
    latestData[symbol] = df;
    def update(attr, old, new):
        selected_expiryDate = expiry_date_selector.value;
        #selectedStrikePrice = allUniqueStrikePrice[strikePrice_selector.active];
        activeStrikePriceIndexes = strikePrice_selector.active; # will take top of selected if number is greater
        activeStrikePriceIndexes.sort(); # starting one will be selected
        index =0;
        selectedStrikeNumber  = activeStrikePriceIndexes.__sizeof__();
        processed = []
        #print(activeStrikePriceIndexes)
        for source in allSources:
            if(index > (selectedStrikeNumber-1)):
                break; # in case less number of strike is selected don't through error
            strikeIndex = activeStrikePriceIndexes[index];
            selectedStrikePrice = allUniqueStrikePrice[strikeIndex];
            new_src = dashboard_tool.make_dataset(int(selectedStrikePrice), selected_expiryDate, symbol, isForTodayOnly)
            source.data.update(new_src.data)
            index = index +1;
            processed.append(selectedStrikePrice);
            #print(selectedStrikePrice) # shown prices are these..
        #print(processed, activeStrikePriceIndexes);

    allUniqueStrikePrice = latestData[symbol]['strikePrice'].apply(str).unique().tolist();
    ATMStrikeindex = int(np.floor(len(allUniqueStrikePrice) / 2))
    expiry_date_selector = Select(value=nearWeekExpiry, options=expiryDates)
    strikePrice_selector = CheckboxButtonGroup(labels=allUniqueStrikePrice, active=[ATMStrikeindex-2,ATMStrikeindex-1, ATMStrikeindex,ATMStrikeindex+1,ATMStrikeindex+2]) # in case multiple to be shown at once#
    # strikePrice_selector = RadioButtonGroup(
    #     labels=allUniqueStrikePrice, active=ATMStrikeindex);
    #
    strikePrice_selector.on_change('active', update)
    expiry_date_selector.on_change('value', update)


    selected_expiryDate = expiry_date_selector.value;
    #selectedStrikePrice = allUniqueStrikePrice[strikePrice_selector.active];

    activeStrikePriceIndexes = strikePrice_selector.active;
    allSources = []
    allplots = []
    for oneindex in activeStrikePriceIndexes:
        selectedStrikePrice = allUniqueStrikePrice[oneindex];
        src = dashboard_tool.make_dataset(int(selectedStrikePrice), selected_expiryDate, symbol, isForTodayOnly)
        allSources.append(src);
        p = dashboard_tool.make_plot(src, selectedStrikePrice)
        allplots.append(p);
    allplotslayout = column(allplots);
    layout = column(row(expiry_date_selector, strikePrice_selector), allplotslayout)
    return layout;

tab = modify_doc();
curdoc().add_root(tab);

