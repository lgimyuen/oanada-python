#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")
import oandaapi as v1
import pandas as pd
import logging
import json
import oandaapi.granularity

from oandamodel.candle import CandleModel
from oandamodel.price import PriceModel
from oandamodel.order import OrderModel
from oandamodel.tool import bollinger_bands, setup_logging

        
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
            df["decimal_place"] = df.precision.str.find("1") - df.precision.str.find(".")

            result = df.to_dict('index')
        
        return (result, status)

  

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
        self._prev_is_close_buy = {}
        self._prev_is_close_sell = {}
        self._prev_is_ask_cross_UB = {}
        self._prev_is_bid_cross_LB = {}

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
                self.on_init(instrument, config)
                self.candles[instrument] = self.candle_model.get_candles(instrument,
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
                    self.candles[instrument] = self.candle_model.get_candles(instrument,
                                        granularity=config["granularity"],
                                        count=config["candles_num"])
                self.on_tick(tick.to_dict(orient="records")[0], self.candles[instrument], config)
            
 
class BollingerStrategy(Strategy):
    def __init__(self, config_data):
        Strategy.__init__(self, config_data)
        

    def on_init(self, instrument, config):
        self._prev_is_close_buy[instrument] = True
        self._prev_is_close_sell[instrument] = True
        self._prev_is_ask_cross_UB[instrument] = True
        self._prev_is_bid_cross_LB[instrument] = True
        

    def on_tick(self, tick, candles, config):
        logger = logging.getLogger("BollingerStrategy.on_tick")
        
        try:
            instrument = tick["instrument"]
            conv_fac = self.get_conv_factor(tick, config)
            
            
            
            #logger.debug(conv_fac)
            #logger.debug({"name": "Tick in Home currency", "bid": tick["bid"]*conv_fac["bid"], "ask": tick["ask"]*conv_fac["ask"]})        
            #use only completed candles
            
            (mu, ub, lb) = bollinger_bands(candles, period=config["bollinger_period"])
            candles = candles[candles.complete]
            
            candle_t1 = Candle(candles, index=-1)
            ub_t1 = ub["closeBid"][-2]
            ub_t0 = ub["closeBid"][-1]
        
            lb_t1 = lb["closeBid"][-2]
            lb_t0 = lb["closeBid"][-1]
        
            stop_loss = round( mu["closeBid"][-1], self.market_info[instrument]["decimal_place"] )

            orders = self.order_model.get_opened( instrument=instrument)
            
            is_no_opened_order = orders is False  or len(orders) == 0

            is_bid_below_MA = tick["bid"] <= stop_loss
            is_ask_above_MA = tick["ask"] >= stop_loss
            is_ask_cross_UB = candle_t1.is_under(ub_t1) and tick["ask"] > ub_t0
            is_bid_cross_LB = candle_t1.is_above(lb_t1) and tick["bid"] < lb_t0

            num_buy_order = 0
            num_sell_order = 0

            if orders is not False and len(orders) > 0:
                num_buy_order = len(orders[orders["side"] == "buy"] )
                num_sell_order = len(orders[orders["side"] == "sell"] ) 

            is_close_buy = num_buy_order > 0 and is_bid_below_MA
            is_close_sell = num_sell_order > 0 and is_ask_above_MA

            account_info = self.get_account_info()
            if account_info == False:
                return


            #long at ask price
            #close at bid price
            buy_stop_gap = tick["bid"] - stop_loss
            buy_stop_gap_home = buy_stop_gap*conv_fac["bid"]
            buy_risk_amt = account_info["marginAvail"]*config["risk"]
            buy_qty = int(buy_risk_amt / buy_stop_gap_home)

            #short at bid price
            #close at ask price
            sell_stop_gap = stop_loss - tick["ask"] 
            sell_stop_gap_home = sell_stop_gap*conv_fac["ask"]
            sell_risk_amt = account_info["marginAvail"]*config["risk"]
            sell_qty = int(sell_risk_amt / sell_stop_gap_home)


            #TODO: Check should close any order?
            #TODO: Check should open any market order?
            
                        
            if is_close_buy:
                self.order_model.close_by_instrument(tick["instrument"])
            if is_close_sell:
                self.order_model.close_by_instrument(tick["instrument"])
                    
            #check order again, ensure they are all closed before proceed
            orders = self.order_model.get_opened( instrument=tick["instrument"])
            
            #wait for next tick to close
            if is_no_opened_order:         
                if is_ask_cross_UB: #Cross Upper Band -> Long
                    (result, status) = self.order_model.send_market_order(tick["instrument"],units=buy_qty, side="buy", stop_loss=stop_loss)                
                    logger.debug({"result": result, "status":status})
                if is_bid_cross_LB: #Cross Lower Band -> Short
                    (result, status) = self.order_model.send_market_order(tick["instrument"],units=sell_qty, side="sell", stop_loss=stop_loss)
                    logger.debug({"result": result, "status":status})



                
            has_state_changed = is_close_buy != self._prev_is_close_buy[instrument] or is_close_sell != self._prev_is_close_sell[instrument] or is_ask_cross_UB != self._prev_is_ask_cross_UB[instrument] or is_bid_cross_LB != self._prev_is_bid_cross_LB[instrument]
            if has_state_changed:
                logger.debug({
                    "tick": tick,
                    "granularity": config["granularity"],
                    "decimal_place": self.market_info[instrument]["decimal_place"],
                    "MA": {
                        "value": stop_loss,
                        "bid_below": is_bid_below_MA,
                        "ask_above": is_ask_above_MA
                    },
                    
                    "cross": {
                        "UB": [ub_t0, ub_t1],
                        "LB": [lb_t0, lb_t1],

                        "ask_above_UB_long": is_ask_cross_UB,
                        "bid_below_LB_short": is_bid_cross_LB

                    },

                    "close":
                    {
                        "buy": is_close_buy,
                        "sell": is_close_sell
                    },

                    "num_orders": {
                        "buy": num_buy_order,
                        "sell": num_sell_order

                    },

                    "candle":{
                        "o": candle_t1.open,
                        "c": candle_t1.close,
                        "h": candle_t1.high,
                        "l": candle_t1.low

                    },

                    "buy_stop_loss":{
                        "buy": buy_stop_gap,
                        "buy_home": buy_stop_gap_home,
                        "risk_amt": buy_risk_amt,
                        "qty": buy_qty


                    },
                    "sell_stop_loss":{
                        "sell": sell_stop_gap,
                        "sell_home": sell_stop_gap_home,
                        "risk_amt": sell_risk_amt,
                        "qty": sell_qty


                    }
                    })
            self._prev_is_close_buy[instrument]  = is_close_buy
            self._prev_is_close_sell[instrument] = is_close_sell
            self._prev_is_ask_cross_UB[instrument] = is_ask_cross_UB
            self._prev_is_bid_cross_LB[instrument] = is_bid_cross_LB


        except Exception as e:
            logger.error(e)
            
        
        
strategy = BollingerStrategy(config_data)        
strategy.run()
