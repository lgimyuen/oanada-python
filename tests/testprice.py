#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1
import json

class TestPrice(unittest.TestCase):
    def setUp(self):
        with open("tests\config.json") as json_data:
                config_data = json.load(json_data)

        v1.API.init(token=config_data["account"]["token"], 
                is_live=config_data["account"]["is_live"],
                account_id=config_data["account"]["account_id"])      
           
    def test_get_prices(self):
       api = v1.Price()
       instruments=["EUR_USD", "USD_SGD"]
       (result, status) = api.get_prices(instruments=instruments)
       
       
       self.assertTrue(status, 200)
       self.assertTrue("prices" in result)
       
       prices = result["prices"]
       for price in prices:
           self.assertTrue("instrument" in price)
           self.assertTrue(price["instrument"] in instruments)
           
    def test_get_prices_stream(self):
       api = v1.Price()
       instruments=["EUR_USD", "USD_SGD"]
       r = api.get_prices_stream(instruments=instruments)
       
       x=0
       y=0
       counter=0
       for line in r:
           self.assertTrue(any(key in line for key in ["heartbeat", "tick"]))
           if "tick" in line:
               if line["tick"]["instrument"] == "EUR_USD":
                   x = x+1
               if line["tick"]["instrument"] == "USD_SGD":
                   y = y+1
           #try 100 times
           if counter > 100:
               break
           
           if x > 1 and y > 1:
               break
       
           counter = counter + 1
           
       self.assertTrue(x>1 and y > 1)
       
           
       
       
           