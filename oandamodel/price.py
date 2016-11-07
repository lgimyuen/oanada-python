# -*- coding: utf-8 -*-
import oandaapi as v1
import pandas as pd
import logging


class PriceModel:
    def __init__(self):
        self.price_api = v1.Price()
    
    def get_prices(self, instruments):
        (res, status) = self.price_api.get_prices(instruments=instruments)
        
        if status == 200:
            p = pd.DataFrame(res["prices"])
            p.set_index("instrument", inplace=True)
            p["time"] = pd.to_datetime(p["time"])
            return (p, status)
            
        return (False, status)
        
    def get_prices_stream(self, instruments):

        logger = logging.getLogger(name="PriceModel.get_prices_stream")
        
        while True:
            try:
                stream = self.price_api.get_prices_stream(instruments=instruments)
                
                for line in stream:
                    if "tick" in line:
                        t = pd.DataFrame([line["tick"]])
                        t["time"] = pd.to_datetime(t["time"])
                        yield t
                    if "heartbeat" in line:
                        logger.debug(line)
            except Exception as e:
                logger.info(e)
                logger.info("Restarting...")
                continue
            
            
