#import os, sys
#sys.path.append(os.path.dirname(__file__) + "/../")

import unittest
import oandaapi as v1



		   

class TestAccount(unittest.TestCase):
    def setUp(self):
        v1.API.init(token="7f53646e2e4c6e99206c3527e7b94037-91ff8c37a8a439b4da5f22be9173b529", 
           is_live=False,
           account_id="7636859")         
        
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