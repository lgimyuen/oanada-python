#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1



		   

class TestInstrument(unittest.TestCase):
    def setUp(self):
        v1.API.init(token="7f53646e2e4c6e99206c3527e7b94037-91ff8c37a8a439b4da5f22be9173b529", 
           is_live=False,
           account_id="7636859")       
           

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