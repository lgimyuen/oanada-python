# -*- coding: utf-8 -*-

import oandaapi as v1
import pandas as pd
import logging
import json
import oandaapi.granularity
from flask import Flask, render_template
import plotly
from plotly.tools import FigureFactory as FF
import numpy as np
import pandas.io.data as web
from datetime import datetime
import plotly.graph_objs as go

from oandamodel.candle import CandleModel
from oandamodel.price import PriceModel
from oandamodel.order import OrderModel
from oandamodel.tool import bollinger_bands




def plotly_instrument(instrument):
    candle_model = CandleModel()
    config = config_data["instruments"][instrument]
    candles = candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"]*4)
    fig = FF.create_candlestick(candles.openBid, candles.highBid, candles.lowBid, candles.closeBid, dates=candles.index)

    (mu, ub, lb) = bollinger_bands(candles, period=config["bollinger_period"])

    ma_line = go.Scatter(
        x=mu.index,
        y=mu.highBid,
        name='Moving Average',
        line=go.Line(color='blue')
        )
    ub_line = go.Scatter(
        x=ub.index,
        y=ub.highBid,
        name='Upper Band',
        line=go.Line(color='green')
        )
    lb_line = go.Scatter(
        x=lb.index,
        y=lb.highBid,
        name='Lower Band',
        line=go.Line(color='green')
        )

    fig['data'].extend([ma_line, ub_line, lb_line])
    layout = dict(
        title="{0} - {1}".format(instrument, config["granularity"]),
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label='1m',
                         step='month',
                         stepmode='backward'),
                    dict(count=6,
                         label='6m',
                         step='month',
                         stepmode='backward'),
                    dict(count=1,
                        label='YTD',
                        step='year',
                        stepmode='todate'),
                    dict(count=1,
                        label='1y',
                        step='year',
                        stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(),
            type='date'
        )
    )
    order_anno = []
    order_model = OrderModel()
    (hist_orders, status) = order_model.get_history(instrument=instrument)
    if status==200 and len(hist_orders)>0:
        hist_orders = hist_orders[hist_orders["type"]!="DAILY_INTEREST"]
        hist_orders = hist_orders[hist_orders["time"] >= candles.index[0]]
    for index, row in hist_orders.iterrows():
        fig['data'].extend([
            go.Scatter(
                x=[row['time']],
                y=[row['price']],
                name='Order',
                text='id: {0}, Order Type: {1}\nSide: {2}'.format(index, row["type"], row['side']),
                mode = 'markers',
                marker = dict(
                    size = 20,
                    color = 'rgba(152, 0, 0, .8)',
                    line = dict(
                        width = 2,
                        color = 'rgb(255, 0, 0)'
                    )
                )
                )
            ])
    """#Use this if want to use Annotations
        order_anno.extend([
            dict(
                x=row['time'],
                y=row['price'],
                xref='x',
                yref='y',
                text='Order Type = {0}'.format(row["type"]),
                showarrow=True,
                arrowhead=7
                )
            ])
    layout["annotations"] = order_anno
    """


    fig['layout'] = layout

    return fig


with open('config.json') as json_data:
    config_data = json.load(json_data)
    print(config_data)

    
v1.API.init(token=config_data["account"]["token"], 
           is_live=config_data["account"]["is_live"],
           account_id=config_data["account"]["account_id"])


           
app = Flask(__name__)

@app.route("/plot_candles/<instrument>")
def plot_candles(instrument):
    
    fig = plotly_instrument(instrument)

    graphs = [fig]



    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)


    return render_template('testplotly.html',
                           ids=ids,
                           graphJSON=graphJSON)


@app.route('/testplotly')
def testplotly():

    df = web.DataReader("aapl", 'yahoo', datetime(2014, 10, 1), datetime(2016, 4, 1))
    fig = FF.create_candlestick(df.Open, df.High, df.Low, df.Close, dates=df.index)
    layout = dict(
        title='Time series with range slider and selectors',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label='1m',
                         step='month',
                         stepmode='backward'),
                    dict(count=6,
                         label='6m',
                         step='month',
                         stepmode='backward'),
                    dict(count=1,
                        label='YTD',
                        step='year',
                        stepmode='todate'),
                    dict(count=1,
                        label='1y',
                        step='year',
                        stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(),
            type='date'
        )
    )

    fig['layout'] = layout
    graphs = [fig]



    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('testplotly.html',
                           ids=ids,
                           graphJSON=graphJSON)

@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/")
def hello():
    price_model = PriceModel()
    instruments = list(config_data["instruments"].keys())
    (prices, status) = price_model.get_prices(instruments)
    
    graphs = []
    for instrument in instruments:
        config = config_data["instruments"][instrument]
        if config["automated_trade"]:
            fig = plotly_instrument(instrument)
            graphs.extend([fig])

    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('testplotly.html',
                           ids=ids,
                           graphJSON=graphJSON)
    
@app.route("/get_candles/<instrument>")
def get_candles(instrument):
    candle_model = CandleModel()
    config = config_data["instruments"][instrument]
    candles = candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"])
    return candles.to_json(orient="index")
            
    
@app.route("/get_trading_instruments")
def get_trading_instruments():
    instruments = list(config_data["instruments"].keys())
    arr = []
    for instrument in instruments:
            config = config_data["instruments"][instrument]
            if config["automated_trade"]:
                arr.append(instrument)
    return ",".join(arr)

@app.route("/get_prices")
def get_prices_default():
    return get_prices('index')
    
@app.route("/get_prices/<orient_type>")
def get_prices(orient_type):
    
    instruments = list(config_data["instruments"].keys())
    price_model = PriceModel()
    (prices, status) = price_model.get_prices(instruments)
    
    return prices.to_json(orient=orient_type)
    

if __name__ == "__main__":
    app.run()
