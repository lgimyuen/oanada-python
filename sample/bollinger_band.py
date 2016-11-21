#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")
import oandaapi as v1
import pandas as pd
import logging
import json
import oandaapi.granularity

from oandamodel.candle import CandleModel
from oandamodel.price import PriceModel

import os
import logging.config

def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
        
setup_logging()

with open('config.json') as json_data:
    config_data = json.load(json_data)
    print(config_data)

    
v1.API.init(token=config_data["account"]["token"], 
           is_live=config_data["account"]["is_live"],
           account_id=config_data["account"]["account_id"])
           
class MarketInfoModel:
    def __init__(self):
        self.instrument_api = v1.Instrument()
    
    def get_market_info(self, instruments=None):
        fields = ["instrument", 
        "pip", 
        "precision", 
        "maxTrailingStop", 
        "minTrailingStop",
        "marginRate", 
        "halted"]
        (result, status) = self.instrument_api.get_instruments(instruments, fields)
        
        if status == 200:
            df = pd.DataFrame.from_dict(result["instruments"])
            df.set_index("instrument", inplace=True)
            result = df.to_dict('index')
        
        return (result, status)


class OrderModel:
    def __init__(self):
        self.trade_api = v1.Trade()
        self.position_api = v1.Position()
        self.order_api = v1.Order()
    
    def get_opened(self, instrument=None, side=None):
        (result, status) = self.trade_api.get_trades(instrument=instrument)
        

        if status == 200:
            orders = pd.DataFrame(result["trades"])
            
            if len(orders.index)>0:
                orders.set_index("id", inplace=True)
                
                if side is not None:
                    return orders[orders["side"] == side]
                else:
                    return orders
            else:
                return orders
        else:
            return False
            
    def close_by_instrument(self, instrument):
        return self.position_api.close_position(instrument=instrument)
        
    def send_market_order(self, instrument, units, side, take_profit=None, stop_loss=None, expiry=None, trailing_stop=None):
        return self.order_api.create_order(instrument, 
                            units=units, side=side, order_type="market", 
                            take_profit=take_profit, stop_loss=stop_loss,
                            trailing_stop=trailing_stop, expiry=expiry)
        
        
        
                

def bollinger_bands(candles, period):
    candles = candles[candles.complete]
    mu = candles.rolling(period).mean()
    sigma = candles.rolling(period).std()
    
    ub = mu+sigma
    lb = mu-sigma    
    
    return (mu, ub, lb)
  
        
#instrument_api = v1.Instrument()
#(instrument, status) = instrument_api.get_instruments(instruments=["EUR_USD"])
candle_model = CandleModel()
price_model = PriceModel()
#prices = price_model.get_prices(["EUR_USD"])

order_model = OrderModel()
orders = order_model.get_opened()


class Candle:
    def __init__(self, candle, candle_type="Bid", index=0):
        self.open = candle["open"+candle_type][index]
        self.close = candle["close"+candle_type][index]
        self.high = candle["high"+candle_type][index]
        self.low = candle["low"+candle_type][index]

    def is_growing(self):
        return self.close > self.open
        
    def is_decreasing(self):
        return self.open > self.close
        
    def is_under(self, value, strict=False):
        if strict:
            return self.high < value
        
        return (self.open < value) and (self.close < value)
    
    def is_above(self, value, strict=False):
        if strict:
            return self.low < value
        
        return (self.open > value) and (self.close > value)
        
    def is_crossing(self, value, strict=False):
        if strict:
            return (self.low <= value) and (self.high >= value)
        return ((self.open <= value) and (self.close >= value)) or ((self.open >=value) and self.close <= value)

    

class Strategy:
    def __init__(self, config_data):
        self.candle_model = CandleModel()
        self.price_model = PriceModel()
        self.order_model = OrderModel()
        
        self.account_api = v1.Account()
        
        self.instruments = list(config_data["instruments"].keys())
        

        self.config_data = config_data
        self.candles = {}
        
        self.marketinfo_model = MarketInfoModel()
        (self.market_info, status) = self.marketinfo_model.get_market_info()
        
        #fetch all the prices first
        #use for conversion of currency to home base
        (self.prices, status) = self.price_model.get_prices(self.instruments)
        
        for instrument in self.instruments:
            config = config_data["instruments"][instrument]   
            #only init trading instrument
            if config["automated_trade"]:
                self.on_init(instrument, config)
                
    def get_account_info(self):
        (acc, status) = self.account_api.get_account()
        if status == 200:
            return acc
        return False
        
    def on_init(self, instrument, config):
        return NotImplemented
    
    def on_tick(self, tick, candles, config):
        return NotImplemented
        
    """
        A_B (A is base currency, B is price currency)
        e.g. How much B per 1 unit of A
        
        Return conversion factor from price currency of quote to home currency
        e.g. How much Home Currency PER 1 unit of Base currency
        
        e.g. AUD_EUR, base currency is EUR, and home currency is SGD,
            this fn return How much SGD(home) per 1 unit of EUR(base)
    """
    def get_conv_factor(self, tick, config):
        if config["home_conversion"]["invert_quote"]:
            quote_bid = 1.0/tick["ask"]
            quote_ask = 1.0/tick["bid"]
        else:
            quote_bid = 1.0
            quote_ask = 1.0
        
        conv = config["home_conversion"]["instrument"]
        if config["home_conversion"]["invert_convert"]:
            conv_bid = 1.0/self.prices["ask"][conv]
            conv_ask = 1.0/self.prices["bid"][conv]
        else:
            conv_bid = self.prices["bid"][conv]
            conv_ask = self.prices["ask"][conv]
            
            return {"conv": "{0} -> {1}".format(tick["instrument"], conv), "bid": quote_bid*conv_bid, "ask": quote_ask*conv_ask}
    
    def run(self):
        for instrument in self.instruments:
            config = config_data["instruments"][instrument]
            if config["automated_trade"]:
                self.candles[instrument] = candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"])
            
        for tick in self.price_model.get_prices_stream(instruments=self.instruments):
            logger = logging.getLogger("Strategy.on_tick")
            logger.debug(tick)
            #print(tick)
            instrument = tick["instrument"][0]
            
            self.prices.loc[instrument, "ask"] = tick["ask"][0]
            self.prices.loc[instrument, "bid"] = tick["bid"][0]
            self.prices.loc[instrument, "time"] = tick["time"][0]
            
            #print(self.prices)
            config = self.config_data["instruments"][instrument]
            
            if config["automated_trade"]:
                granularity = config["granularity"]
    
                time_delta = tick["time"] - self.candles[instrument].index[-1]            
                if ( time_delta > oandaapi.granularity.to_timedelta(granularity) ).bool():
                    self.candles[instrument] = candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"])
                self.on_tick(tick.to_dict(orient="records")[0], self.candles[instrument], config)
            
 
class BollingerStrategy(Strategy):
    def on_init(self, instrument, config):
        return NotImplemented
        

    def on_tick(self, tick, candles, config):
        logger = logging.getLogger("BollingerStrategy.on_tick")
        
        try:
            conv_fac = self.get_conv_factor(tick, config)
            
            
            
            #logger.debug(conv_fac)
            #logger.debug({"name": "Tick in Home currency", "bid": tick["bid"]*conv_fac["bid"], "ask": tick["ask"]*conv_fac["ask"]})        
            #use only completed candles
            candles = candles[candles.complete]
            (mu, ub, lb) = bollinger_bands(candles, period=config["bollinger_period"])
            
            candle_t1 = Candle(candles, index=-1)
            ub_t1 = ub["closeBid"][-2]
            ub_t0 = ub["closeBid"][-1]
        
            lb_t1 = lb["closeBid"][-2]
            lb_t0 = lb["closeBid"][-1]
        
            stop_loss = mu["closeBid"][-1]

            orders = self.order_model.get_opened( instrument=tick["instrument"])
            

            is_bid_below_MA = tick["bid"] <= stop_loss
            is_ask_above_MA = tick["ask"] >= stop_loss
            is_ask_cross_UB = candle_t1.is_under(ub_t1) and tick["ask"] > ub_t0
            is_ask_cross_LB = candle_t1.is_above(lb_t1) and tick["bid"] < lb_t0

            logger.debug({
                "instrument": tick["instrument"],
                "granularity": config["granularity"],
                "is_bid_below_MA": is_bid_below_MA,
                "is_ask_above_MA": is_ask_above_MA,
                "is_ask_cross_above_UB": is_ask_cross_UB,
                "is_ask_cross_below_LB": is_ask_cross_LB
                })
            #TODO: Check should close any order?
            #TODO: Check should open any market order?
            
            
            
            if orders is not False and len(orders) > 0:
                if len(orders[orders["side"] == "buy"] ) > 0 and is_bid_below_MA:
                    self.order_model.close_by_instrument(tick["instrument"])
                if len(orders[orders["side"] == "sell"] ) > 0 and is_ask_above_MA:
                    self.order_model.close_by_instrument(tick["instrument"])
                    
            #check order again, ensure they are all closed before proceed
            orders = self.order_model.get_opened( instrument=tick["instrument"])
            
            #wait for next tick to close
            if orders is not False  and len(orders) > 0:
                return
                   
        
            account_info = self.get_account_info()
            if account_info == False:
                return
            #logger.debug(account_info)    
            
            
            
                
            if is_ask_cross_UB:
                #long at ask price
                #close at bid price
                stop_gap = tick["bid"] - stop_loss
                stop_gap_home = stop_gap*conv_fac["bid"]
                risk_amt = account_info["marginAvail"]*config["risk"]
                qty = int(risk_amt / stop_gap_home)
                self.order_model.send_market_order(tick["instrument"],units=qty, side="buy", stop_loss=stop_loss)
                logger.info("go long, stop gap =  {0}, qty = {1}".format(stop_gap, qty))
                
            if is_ask_cross_LB:
                #short at bid price
                #close at ask price
                stop_gap = stop_loss - tick["ask"] 
                stop_gap_home = stop_gap*conv_fac["ask"]
                risk_amt = account_info["marginAvail"]*config["risk"]
                qty = int(risk_amt / stop_gap_home)
                self.order_model.send_market_order(tick["instrument"],units=qty, side="sell", stop_loss=stop_loss)
                logger.info("go short, stop gap =  {0}, qty = {1}".format(stop_gap, qty))
        except Exception as e:
            logger.error(e)
            
        
        
strategy = BollingerStrategy(config_data)        
strategy.run()

"""
data = {}
for instrument in config_data["instruments"]:    
    name = instrument["instrument"]
    data[name] = {}
    data[name]["period"] = instrument["bollinger_period"]
    data[name]["granularity"] = instrument["granularity"]

    data[instrument["instrument"]]["candles"] = candle_model.get_candles(instrument["instrument"],
                                    granularity=instrument["granularity"],
                                    count=instrument["bollinger_period"]+3)
       
    (data[instrument["instrument"]]["mu"],
     data[instrument["instrument"]]["ub"],
     data[instrument["instrument"]]["lb"]) = bollinger_bands(
                            data[instrument["instrument"]]["candles"], 
                            period=instrument["bollinger_period"])

#since_time = datetime.datetime(2016, 10, 13)
#since_time.isoformat("T")
logger = logging.getLogger("bollinger_band.py")

for tick in price_model.get_prices_stream(instruments=list(data.keys())):
    name = tick["instrument"][0]
    candles = data[name]["candles"]
    ub = data[name]["ub"]
    lb = data[name]["lb"]
    mu = data[name]["mu"]
    granularity = data[name]["granularity"]
    period = data[name]["period"]

    time_delta = tick["time"] - candles.index[-1]
    logger.debug("{0} time since last candle {1}".format(tick["instrument"][0], time_delta[0]))
    
    if ( time_delta > oandaapi.granularity.to_timedelta(granularity) ).bool():
        logger.debug("{0} fetching candles".format(tick["instrument"][0]))
        
        data[name]["candles"] = candle_model.get_candles(name, 
                    granularity=granularity, 
                    count=period+3)
        candles = data[name]["candles"] #is this really needed?

        (data[name]["mu"], 
         data[name]["ub"], 
         data[name]["lb"]) = bollinger_bands(candles, period=period)
        
        (mu, ub, lb) = (data[name]["mu"], data[name]["ub"], data[name]["lb"])
        
    if (tick["bid"] < lb["closeBid"].tail(1)).bool():
        logger.debug("Short {0}".format(tick["instrument"][0]))
    elif (tick["ask"] > ub["closeAsk"].tail(1)).bool():
        logger.debug("Long {0}".format(tick["instrument"][0]))
    

"""
