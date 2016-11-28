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
from datetime import datetime
import plotly.graph_objs as go

from oandamodel.candle import CandleModel
from oandamodel.price import PriceModel
from oandamodel.order import OrderModel
from oandamodel.tool import bollinger_bands




def plotly_instrument(instrument, config):
    candle_model = CandleModel()
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

    print(candles.tail(1))
    fig['data'].extend([ma_line, ub_line, lb_line])
    layout = dict(
        title="{0} - {1}".format(instrument, config["granularity"]),
        shapes=[
            dict(
                type='line',
                x0=candles.index[0],
                x1=candles.index[-1],
                y0=candles.closeBid[-1],
                y1=candles.closeBid[-1],
                line=dict(color='rgb(255,0,0)')
                ),
            dict(
                type='line',
                x0=candles.index[0],
                x1=candles.index[-1],
                y0=candles.closeAsk[-1],
                y1=candles.closeAsk[-1],
                line=dict(color='rgb(0,0,255)')
                )
        ],
        yaxis=dict(fixedrange=False)

    )
    """
    layout = dict(
        title="{0} - {1}".format(instrument, config["granularity"]),
        shapes=[
            dict(
                type='line',
                x0=candles.index[0],
                x1=candles.index[-1],
                y0=candles.closeBid[-1],
                y1=candles.closeBid[-1],
                line=dict(color='rgb(255,0,0)')
                ),
            dict(
                type='line',
                x0=candles.index[0],
                x1=candles.index[-1],
                y0=candles.closeAsk[-1],
                y1=candles.closeAsk[-1],
                line=dict(color='rgb(0,0,255)')
                )
        ],
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
        ),
        yaxis=dict(fixedrange=False)

    )"""
    #order_anno = []
    order_model = OrderModel()
    (hist_orders, status) = order_model.get_history(instrument=instrument)
    if status==200 and len(hist_orders)>0:
        hist_orders = hist_orders[hist_orders["type"]!="DAILY_INTEREST"]
        hist_orders = hist_orders[hist_orders["time"] >= candles.index[0]]

    market_order_buy_x = []
    market_order_buy_y = []
    market_order_sell_x = []
    market_order_sell_y = []
    market_order_buy_text = []
    market_order_sell_text = []


    stop_loss_filled_buy_x = []
    stop_loss_filled_buy_y = []

    stop_loss_filled_sell_x = []
    stop_loss_filled_sell_y = []

    trade_close_buy_x = []
    trade_close_buy_y = []

    trade_close_sell_x = []
    trade_close_sell_y = []

    for index, row in hist_orders.iterrows():
        if row["type"] == "MARKET_ORDER_CREATE":
            if row["side"] == "buy":
                market_order_buy_x.extend([row["time"]])
                market_order_buy_y.extend([row["price"]])
                market_order_buy_text.extend([index])
            else:
                market_order_sell_x.extend([row["time"]])
                market_order_sell_y.extend([row["price"]])
                market_order_sell_text.extend([index])

        if row["type"] == "STOP_LOSS_FILLED":
            if row["side"] == "buy":
                stop_loss_filled_buy_x.extend([row["time"]])
                stop_loss_filled_buy_y.extend([row["price"]])
            else:
                stop_loss_filled_sell_x.extend([row["time"]])
                stop_loss_filled_sell_y.extend([row["price"]])
        if row["type"] == "TRADE_CLOSE":
            if row["side"] == "buy":
                trade_close_buy_x.extend([row["time"]])
                trade_close_buy_y.extend([row["price"]])
            else:
                trade_close_sell_x.extend([row["time"]])
                trade_close_sell_y.extend([row["price"]])

    fig['data'].extend([
        go.Scatter(
            x=market_order_buy_x,
            y=market_order_buy_y,
            name='Market Order LONG',
            text=market_order_buy_text,
            mode = 'markers',
            marker = dict(
                size = 20,
                color = 'rgba(0, 152, 0, .8)',
                symbol = "triangle-up",
                line = dict(
                    width = 2,
                    color = 'rgb(0, 255, 0)'
                )
            )),
        go.Scatter(
            x=market_order_sell_x,
            y=market_order_sell_y,
            name='Market Order SHORT',
            text=market_order_sell_text,
            mode = 'markers',
            marker = dict(
                size = 20,
                symbol = 'triangle-down',
                color = 'rgba(152, 0, 0, .8)',
                line = dict(
                    width = 2,
                    color = 'rgb(255, 0, 0)'
                )
            )),
        go.Scatter(
            x=stop_loss_filled_buy_x,
            y=stop_loss_filled_buy_y,
            name='STOP LOSS LONG',
            #text='id: {0}, Order Type: {1}\nSide: {2}'.format(index, row["type"], row['side']),
            mode = 'markers',
            marker = dict(
                size = 20,
                color = 'rgba(0, 0, 152, .8)',
                line = dict(
                    width = 2,
                    color = 'rgb(255, 0, 0)'
                )
            )),
        go.Scatter(
            x=stop_loss_filled_sell_x,
            y=stop_loss_filled_sell_y,
            name='STOP LOSS SHORT',
            #text='id: {0}, Order Type: {1}\nSide: {2}'.format(index, row["type"], row['side']),
            mode = 'markers',
            marker = dict(
                size = 20,
                color = 'rgba(152, 0, 152, .8)',
                line = dict(
                    width = 2,
                    color = 'rgb(255, 0, 0)'
                )
            )),
        go.Scatter(
            x=trade_close_buy_x,
            y=trade_close_buy_y,
            name='TRADE CLOSE LONG',
            #text='id: {0}, Order Type: {1}\nSide: {2}'.format(index, row["type"], row['side']),
            mode = 'markers',
            marker = dict(
                size = 20,
                color = 'rgba(152, 0, 152, .8)',
                line = dict(
                    width = 2,
                    color = 'rgb(255, 0, 0)'
                )
            )),
        go.Scatter(
            x=trade_close_sell_x,
            y=trade_close_sell_y,
            name='TRADE CLOSE SHORT',
            #text='id: {0}, Order Type: {1}\nSide: {2}'.format(index, row["type"], row['side']),
            mode = 'markers',
            marker = dict(
                size = 20,
                color = 'rgba(0, 100, 100, .8)',
                line = dict(
                    width = 2,
                    color = 'rgb(255, 0, 0)'
                )
            ))

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

def init_sys():
    with open('config.json') as json_data:
        config_data = json.load(json_data)
        print(config_data)

        
    v1.API.init(token=config_data["account"]["token"], 
               is_live=config_data["account"]["is_live"],
               account_id=config_data["account"]["account_id"])

    return config_data

           
app = Flask(__name__)


@app.route("/")
def root():
    config_data = init_sys()

    price_model = PriceModel()
    instruments = list(config_data["instruments"].keys())
    (prices, status) = price_model.get_prices(instruments)
    
    graphs = []
    for instrument in instruments:
        config = config_data["instruments"][instrument]
        if config["automated_trade"]:
            fig = plotly_instrument(instrument, config_data["instruments"][instrument])
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
    config_data = init_sys()

    candle_model = CandleModel()
    config = config_data["instruments"][instrument]
    candles = candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"])
    return candles.to_json(orient="index")
            
    
@app.route("/get_trading_instruments")
def get_trading_instruments():
    config_data = init_sys()

    instruments = list(config_data["instruments"].keys())
    arr = []
    for instrument in instruments:
            config = config_data["instruments"][instrument]
            if config["automated_trade"]:
                arr.append(instrument)
    return ",".join(arr)

@app.route("/get_prices")
def get_prices_default():
    config_data = init_sys()
    return get_prices('index')
    
@app.route("/get_prices/<orient_type>")
def get_prices(orient_type):
    config_data = init_sys()

    instruments = list(config_data["instruments"].keys())
    price_model = PriceModel()
    (prices, status) = price_model.get_prices(instruments)
    
    return prices.to_json(orient=orient_type)
    

if __name__ == "__main__":
    app.run()
