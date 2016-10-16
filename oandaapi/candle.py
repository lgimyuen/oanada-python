# -*- coding: utf-8 -*-
from oandaapi.api import API
#import requests

class Candle(API):
    def get_candles(self, instrument, 
                    granularity=None, count=None, 
                    start=None, end=None, 
                    candleFormat=None, includeFirst=None, dailyAlignment=None,
                    alignmentTimezone=None, weeklyAlignment=None):
        params = {"instrument": instrument}
        
        if granularity is not None:
            params["granularity"] = granularity
        
        if count is not None:
            params["count"] = count
        
        
        r = self.get(action="candles", params=params)
        
        #convert to pandas dataframe
#        if r.status_code == requests.status_codes.codes.ok:
#            j = r.json()
#            c = pd.DataFrame(j["candles"])
#            c["time"] = pd.to_datetime(c["time"])
#            c = c.set_index("time")
#            return (c, r.status_code)
        return (r.json(), r.status_code)