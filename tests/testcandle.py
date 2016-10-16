# -*- coding: utf-8 -*-

#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1



		   

class TestCandle(unittest.TestCase):
    def setUp(self):
        v1.API.init(token="7f53646e2e4c6e99206c3527e7b94037-91ff8c37a8a439b4da5f22be9173b529", is_live=False, account_id="7636859")    
    
    def test_get_candles(self):
        api = v1.Candle()
        (r, status)=api.get_candles(instrument="EUR_USD", granularity="H4")
        
        self.assertEqual(status, 200)
        self.assertEqual(r["instrument"], "EUR_USD")
        self.assertEqual(r["granularity"], "H4")
        self.assertGreater(len(r["candles"]), 0)
   
           