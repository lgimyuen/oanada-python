# -*- coding: utf-8 -*-
import oandaapi as v1
import pandas as pd
import logging

class OrderModel:
    def __init__(self):
        self.trade_api = v1.Trade()
        self.position_api = v1.Position()
        self.order_api = v1.Order()
        self.transaction_api = v1.Transaction()
    def get_history(self, instrument=None):
        (result, status) = self.transaction_api.get_transactions(instrument=instrument)
        if status == 200:
            orders = pd.DataFrame(result["transactions"])
            if len(orders.index)>0:
                orders["time"] = pd.to_datetime(orders["time"])
                orders.set_index("id", inplace=True)
            return (orders, status)
        else:
            return (False, status)
    
    def get_opened(self, instrument=None, side=None):
        logger = logging.getLogger("OrderModel.get_opened")

        (result, status) = self.trade_api.get_trades(instrument=instrument)

        logger.debug({"instrument":instrument, "side":side, "result": result, "status": status})

        if status == 200:
            orders = pd.DataFrame(result["trades"])
            
            if len(orders.index)>0:
                orders.set_index("id", inplace=True)
                orders["time"] = pd.to_datetime(orders["time"])
                
                if side is not None:
                    return orders[orders["side"] == side]
                else:
                    return (orders, status)
            else:
                return (orders, status)
        else:
            return (False, status)
            
    def close_by_instrument(self, instrument):
        return self.position_api.close_position(instrument=instrument)

    def send_market_order(self, instrument, units, side, take_profit=None, stop_loss=None, expiry=None, trailing_stop=None):
        return self.order_api.create_order(instrument, 
                            units=units, side=side, order_type="market", 
                            take_profit=take_profit, stop_loss=stop_loss,
                            trailing_stop=trailing_stop, expiry=expiry)

    def modify_opened_order(self, order_id,
                    stop_loss = None,
                    take_profit=None,
                    trailing_stop = None):
        return self.order_api.patch_trade(order_id,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        trailing_stop=trailing_stop)