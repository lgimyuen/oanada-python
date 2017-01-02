# -*- coding: utf-8 -*-

#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1

import json

		   

class TestCandle(unittest.TestCase):
    def setUp(self):
        with open("tests\config.json") as json_data:
                config_data = json.load(json_data)

        v1.API.init(token=config_data["account"]["token"], 
                is_live=config_data["account"]["is_live"],
                account_id=config_data["account"]["account_id"])      
    
    def test_get_candles(self):
        api = v1.Candle()
        (r, status)=api.get_candles(instrument="EUR_USD", granularity="H4")
        
        self.assertEqual(status, 200)
        self.assertEqual(r["instrument"], "EUR_USD")
        self.assertEqual(r["granularity"], "H4")
        self.assertGreater(len(r["candles"]), 0)
   
           