from oandaapi.api import API

class Transaction(API):
    def get_transactions(self, maxId=None, minId=None, count=None, instrument=None, ids=None):
        params={}
        if instrument is not None:
            params["instrument"] = instrument
            
        r = self.get(action="/".join(["accounts", self.account_id, "transactions"]), params=params)
        return (r.json(), r.status_code)