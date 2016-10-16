from oandaapi.api import API
"""
# Order is before trade/position is opened    
# if order is filled, then it will appear in trade and position

"""
class Order(API):
    def get_orders(self):
        r = self.get(action="/".join(["accounts", self.account_id, "orders"]))
        return (r.json(), r.status_code)
    
    def get_order(self, order_id):
        r = self.get(action="/".join(["accounts", self.account_id, "orders", str(order_id)]))
        return (r.json(), r.status_code)
    
    def delete_order(self, order_id):
        r = self.delete(action="/".join([
                    "accounts", 
                    self.account_id, 
                    "orders", 
                    str(order_id)
                ]))
        return (r.json(), r.status_code)
    
    def patch_order(self, order_id, units=None,
                    price=None, expiry=None,
                    lower_bound=None,
                    upper_bound=None,
                    stop_loss = None,
                    take_profit=None,
                    trailing_stop = None
                   ):
        data = {}
        if units is not None:
            data["units"] = units
            
        if price is not None:
            data["price"] = price
            
        if lower_bound is not None:
            data["lowerBound"] = lower_bound
            
        if upper_bound is not None:
            data["upperBound"] = upper_bound
            
        if take_profit is not None:
            data["takeProfit"] = take_profit
        
        if stop_loss is not None:
            data["stopLoss"] = stop_loss
            
        if trailing_stop is not None:
            data["trailingStop"] = trailing_stop
            
        r = self.patch(action="/".join([
                    "accounts",
                    self.account_id,
                    "orders",
                    str(order_id)
                ]), data=data)
        return (r.json(), r.status_code)
    
    def create_order(self, instrument, units, side, order_type, 
               expiry=None, price=None, lower_bound=None,
               upper_bound=None, stop_loss=None, take_profit=None,
               trailing_stop=None
              ):
        
        data = {
            "instrument": instrument,
            "units": units,
            "side": side,
            "type": order_type            
        }
        
        #Sanity check
        if any(x == order_type for x in ["market", "limit", "stop", "marketIfTouched"]) == False:
            raise Exception("Only [market, limit, stop, marketIfTouched] is allowed")
            
        if any(x == order_type for x in ["limit", "stop", "marketIfTouched"]) == True:
            if expiry is None:
                raise Exception("non market order needs an expiry date")
            if price is None:
                raise Exception("non market order needs a price")
            data["expiry"] = expiry
            data["price"] = price
        
        if take_profit is not None:
            data["takeProfit"] = take_profit
        
        if stop_loss is not None:
            data["stopLoss"] = stop_loss
            
        if trailing_stop is not None:
            data["trailingStop"] = trailing_stop
        
        r = self.post(action="/".join(["accounts", self.account_id, "orders"]), data=data)
        return (r.json(), r.status_code)
    