# -*- coding: utf-8 -*-
from oandaapi.api import API
import json
import requests

class Price(API):
        
    def get_prices(self, instruments, since=None):
        params = {}
        params["instruments"] = ",".join(instruments)

        if since is not None:
            params["since"] = since
            
        r = self.get(action="prices", params=params)
        return (r.json(), r.status_code)
        
    def get_prices_stream(self, instruments):
        params={}
        params["instruments"] = ",".join(instruments)
        
        r = self.get(action="prices", params=params, stream=True)
        
        if r.status_code != requests.status_codes.codes.ok:
            return False
            
        lines = r.iter_lines()
        first_line = next(lines)
        
        yield json.loads(first_line.decode("utf-8"))
    
        for line in lines:
            if line:
                yield json.loads(line.decode("utf-8"))
        