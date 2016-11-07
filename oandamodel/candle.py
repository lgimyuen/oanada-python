# -*- coding: utf-8 -*-
import oandaapi as v1
import pandas as pd

class CandleModel:
    def __init__(self):
        self.api = v1.Candle()
    
    def get_candles(self, instrument, granularity="H4", count=103):
        (result, status) = self.api.get_candles(instrument=instrument, granularity=granularity, count=count)
        
        if status == 200:
            c = pd.DataFrame(result["candles"])
            c["time"] = pd.to_datetime(c["time"])
            c = c.set_index("time")
            return c
        return False
        