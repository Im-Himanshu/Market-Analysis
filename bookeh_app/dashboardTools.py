from bokeh.io import output_file, show
from bokeh.models import RangeSlider,Select
from bokeh.io import show, output_notebook, push_notebook
from bokeh.plotting import figure

from bokeh.models import CategoricalColorMapper, HoverTool, ColumnDataSource, Panel, LinearAxis, Range1d
from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, DateRangeSlider, CheckboxButtonGroup,RadioButtonGroup

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




class UIutility :
    optionUtility = 0;
    symbols = [];
    tableprefix="";

    def __init__(self, optionUtility, symbols,tablePrefix):
        self.optionUtility =optionUtility;
        self.symbols = symbols;
        self.tableprefix = tablePrefix;



    def make_dataset(self, strike_prices, expiry_date, symbol, onlyTodayData):
        today = DT.datetime.now().strftime("%m/%d/%Y")
        if (type(strike_prices) == int):
            strike_prices = "(" + str(
                strike_prices) + ")"  ## in case tuple length is one it treats it as one single variable
        rawQuery = "SELECT * FROM {tableName} WHERE strikePrice in {strikePrices} AND expiryDate='{expiryDate}'"
        # remove the expiry date clause if all have to be shown
        if (expiry_date == "All Above"):
            rawQuery = rawQuery.split(' AND expiryDate')[0];
        if(onlyTodayData):
            rawQuery = rawQuery+" AND timestamp > '{todayDate}'"
        query = rawQuery.format(tableName=self.tableprefix + symbol, strikePrices=str(strike_prices),
                                expiryDate=expiry_date,todayDate=today);
        df = self.optionUtility.executeSQLQuery(query);
        df = df.drop(columns=['impliedVolatility', 'expiryDate', 'changeinOpenInterest', 'change',
                              'totalTradedVolume', 'totalBuyQuantity', 'totalSellQuantity'])
        df['timestamp'] = df['timestamp'].apply(pd.to_datetime);
        df['timestamp2']  =df.timestamp.dt.strftime('%H:%M').astype(str)#converting it to string for inear scale..
        ## have to work on this logic
        if (expiry_date == "All Above"):
            df = df.groupby(['timestamp', 'strikePrice', 'types'], as_index=False)['openInterest'].sum();
        df = df.drop_duplicates(subset=['strikePrice', 'timestamp', 'types'],
                                keep='last');  # removing the duplicate entries
        # assuming only one strike price is passed at a time as of now
        callPut_df = []
        grouped = df.groupby('types');
        for name, group in grouped:
            group = group.rename(
                columns={"openInterest": name + "_OI"})  # "changeinOpenInterest" :name+"_OI change"
            callPut_df.append(group)
        callPutMerged_df = pd.merge(callPut_df[0], callPut_df[1],
                                    left_on=['strikePrice', 'underlyingPrice', 'timestamp','timestamp2'],
                                    right_on=['strikePrice', 'underlyingPrice',
                                              'timestamp','timestamp2'])  # assuming strike_price is same, expiry_date is same
        callPutMerged_df = callPutMerged_df.sort_values(['timestamp'])
        return ColumnDataSource(callPutMerged_df);

    def style(self, p):
        # Title
        p.title.align = 'center'
        p.title.text_font_size = '10pt'
        p.title.text_font = 'serif'

        # Axis titles
        p.xaxis.axis_label_text_font_size = '4pt'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.yaxis.axis_label_text_font_size = '4pt'
        p.yaxis.axis_label_text_font_style = 'bold'

        # Tick labels
        p.xaxis.major_label_text_font_size = '6pt'
        p.yaxis.major_label_text_font_size = '6pt'

        return p

    def make_plot(self, src, strikePrice):
        hover = HoverTool(tooltips=[
            #('Int. Val. call', '@internalValue_x'),
            #('Int. Val. put', '@internalValue_y'),
            ('Underlying Price', '@underlyingPrice'),
            ('Strike Price', '@strikePrice'),
            ('timing', '@timestamp2')
        ],
            mode='vline')

        p = figure(plot_width=400, plot_height=400,
                   title='OI call : ', x_axis_type='datetime',
                   x_axis_label='Time', y_axis_label='OI(in # of contract)')

        p.line('timestamp', 'CE_OI', source=src, color="firebrick", line_width=4, alpha=0.7, legend_label="Call OI")
        p.circle('timestamp', 'CE_OI', source=src, fill_color="white", size=4);
        p.line('timestamp', 'PE_OI', source=src, color="navy", line_width=4, alpha=0.7, legend_label="Put OI")
        p.circle('timestamp', 'PE_OI', source=src, fill_color="white", size=4)

        # p.line('timestamp', 'PE_OI', source=src, color="navy", line_width=4, alpha=0.3, legend_label="Put OI")
        # p.circle('timestamp', 'PE_OI', source=src, fill_color="white", size=4)
        # p.extra_y_ranges = {"foo": Range1d(start=0, end=400),"ltp": Range1d(start=0, end=400)}
        # p.circle(src.data['timestamp'], src.data['lastPrice_x'], color="yellow", y_range_name="foo")
        # p.line('timestamp', 'lastPrice_x', source=src, color="blue", y_range_name="ltp", line_width=4,legend_label="LTP")
        # p.add_layout(LinearAxis(y_range_name="ltp"), 'left')
        p.add_tools(hover)


        p = self.style(p)
        p1 = p


        #-----
        # p = figure(plot_width=400, plot_height=400,
        #            title='OI Put :' + strikePrice, x_axis_type='datetime',
        #            x_axis_label='Time', y_axis_label='OI(in # of Contracts)')
        # p.line('timestamp', 'PE_OI', source=src, color="navy", line_width=4, alpha=0.7, legend_label="Put OI")
        # p.circle('timestamp', 'PE_OI', source=src, fill_color="white", size=4)
        #
        # p.add_tools(hover)
        #
        # p = self.style(p)
        # p2 = p
        ## -------

        p = figure(plot_width=400, plot_height=400,
                   title='External value :', x_axis_type='datetime',
                   x_axis_label='Time', y_axis_label='OI(in # of Contracts)')
        # p.line('timestamp', 'lastPrice_x', source=src, color="red", line_width=4, alpha=0.7, legend_label="call ltp")
        #p.line('timestamp', 'lastPrice_y', source=src, color="navy", line_width=4,alpha=0.7,legend_label="put ltp")
        p.line('timestamp', 'externalValue_x', source=src, color="red", line_width=4, alpha=0.3, legend_label="CE ext.")
        p.line('timestamp', 'externalValue_y', source=src, color="navy", line_width=4,alpha=0.3, legend_label="PE ext")

        p.add_tools(hover)
        p = self.style(p)
        p3 = p


        #----
        p = figure(plot_width=400, plot_height=400,
                   title='LTP :', x_axis_type='datetime',
                   x_axis_label='Time', y_axis_label='OI(in # of Contracts)')
        p.line('timestamp', 'lastPrice_x', source=src, color="red", line_width=4, alpha=0.7, legend_label="call ltp")
        p.line('timestamp', 'lastPrice_y', source=src, color="navy", line_width=4,alpha=0.7,legend_label="put ltp")
        p4 = p

        return row(p1,p3,p4)

