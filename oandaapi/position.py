from oandaapi.api import API

"""
# Check all opened position
"""
class Position(API):
    def get_position(self, instrument):
        r = self.get(action="/".join(["accounts", self.account_id, "positions", instrument]))
        return (r.json(), r.status_code)
        
    
    def get_positions(self):
        r = self.get(action="/".join(["accounts", self.account_id, "positions"]))
        return (r.json(), r.status_code)
    
    def close_position(self, instrument):
        r = self.delete(action="/".join([
                    "accounts", 
                    self.account_id, 
                    "positions",
                    instrument
                ]))
        return (r.json(), r.status_code)