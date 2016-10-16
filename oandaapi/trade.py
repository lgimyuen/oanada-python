from oandaapi.api import API

class Trade(API):
    def get_trades(self, instrument=None, max_count=None, count_per_page=None, ids=None):
        params = {}
        
        if instrument is not None:
            params["instrument"] = instrument
        
        r = self.get(action="/".join(["accounts", self.account_id, "trades"]), params=params)
        return (r.json(), r.status_code)
        
    
    def get_trade(self, trade_id):
        pass