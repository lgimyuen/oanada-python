#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1
import json


		   

class TestInstrument(unittest.TestCase):
    def setUp(self):
        with open("tests\config.json") as json_data:
                config_data = json.load(json_data)

        v1.API.init(token=config_data["account"]["token"], 
                is_live=config_data["account"]["is_live"],
                account_id=config_data["account"]["account_id"])      
           

    def test_get_instruments(self):
        api = v1.Instrument()
        (instruments, status) = api.get_instruments()
        
        self.assertEqual(status, 200)
        self.assertGreater(len(instruments["instruments"]), 0)
        
    def test_get_instrument(self):
        api = v1.Instrument()
        (instruments, status) = api.get_instruments(instruments=["EUR_USD", "USD_SGD"])
        
        self.assertEqual(status, 200)
        self.assertEqual(len(instruments["instruments"]), 2)
        
        for instrument in instruments["instruments"]:
            self.assertTrue(instrument["instrument"] in ["EUR_USD", "USD_SGD"])
            
    def test_get_instrument_with_fields(self):
        api = v1.Instrument()
        (instruments, status) = api.get_instruments(instruments=["EUR_USD", "USD_SGD"], fields=["instrument", "pip"])
        
        self.assertEqual(status, 200)
        self.assertEqual(len(instruments["instruments"]), 2)
        
        for instrument in instruments["instruments"]:
            self.assertTrue("pip" in instrument)
            self.assertTrue("instrument" in instrument)
            self.assertTrue(instrument["instrument"] in ["EUR_USD", "USD_SGD"])

if __name__ == '__main__':
    unittest.main()