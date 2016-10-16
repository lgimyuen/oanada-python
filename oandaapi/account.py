from oandaapi.api import API

class Account(API):
    
    def get_accounts(self):
        r = self.get(action="accounts")
        return (r.json(), r.status_code)
    
    def get_account(self):        
        
        r = self.get(action="/".join(["accounts", self.account_id]))
        return (r.json(), r.status_code)