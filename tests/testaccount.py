#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1
import json


		   

class TestAccount(unittest.TestCase):
    def setUp(self):
        with open("tests\config.json") as json_data:
                config_data = json.load(json_data)

        v1.API.init(token=config_data["account"]["token"], 
                is_live=config_data["account"]["is_live"],
                account_id=config_data["account"]["account_id"])         
        
    def test_get_accounts(self):
        api = v1.Account()
        (accs, status) = api.get_accounts()

        self.assertEqual(status, 200, msg = "get_accounts status fails")
        self.assertTrue("accounts" in accs, msg="get_accounts fail to return accounts")
        
        for account in accs["accounts"]:
            self.assertTrue("accountId" in account, msg="No account ID given")
    
    def test_get_account(self):
        api = v1.Account()
        (accs, status) = api.get_accounts()
        
        self.assertEqual(status, 200, msg = "get_accounts status fails")
        
if __name__ == '__main__':
    unittest.main()