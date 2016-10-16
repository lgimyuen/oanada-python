import requests
import logging
#import imp
import json

#for ipython to display. need to reload loggin
#imp.reload(logging)
logging.basicConfig(level=logging.DEBUG)

class API:
    api_token = None
    is_live = False
    PRAC_HOST = "https://api-fxpractice.oanda.com"
    PRAC_STREAM_HOST = "https://stream-fxpractice.oanda.com"
    LIVE_HOST = "https://api-fxtrade.oanda.com"
    LIVE_STREAM_HOST = "https://stream-fxtrade.oanda.com"
    api_type = "v1"
    api = None
    host = None
    stream_host = None
    account_id = None
    api_action = None
    
    @classmethod
    def init(self, token, is_live=False, account_id=None):
        self.api_token = token
        if(is_live == True):
            self.host = self.LIVE_HOST
            self.stream_host = self.LIVE_STREAM_HOST
        else:
            self.host = self.PRAC_HOST
            self.stream_host = self.PRAC_STREAM_HOST
            
        if account_id is not None:
            self.account_id = account_id
    
    def get(self, action=None, params={}, stream=False):
        if action is not None:
            self.api_action = action
        logger = logging.getLogger("OandaAPI.get")
        
        if stream is True:
            host = self.stream_host
        else:
            host  = self.host
        self.api = "/".join([host, self.api_type, self.api_action])
        logger.debug(self.api)
        
        if self.account_id is not None:
            params["accountId"] = self.account_id
        r = requests.get(self.api, headers={"Authorization": "Bearer "+self.api_token}, params=params, stream=stream)
        
        logger.debug(r.status_code)
        if r.status_code != requests.status_codes.codes.ok:
            logger.warning(r.text)
        
        return r
    
    def post(self, action=None, params={}, data={}):
        if action is not None:
            self.api_action = action
        logger = logging.getLogger("OandaAPI.post")
        self.api = "/".join([self.host, self.api_type, self.api_action])
        logger.debug(self.api)
        logger.debug(data)
        
        if self.account_id is not None:
            params["accountId"] = self.account_id
        r = requests.post(self.api, headers={"Authorization": "Bearer "+self.api_token}, params=params, data=data)
        
        logger.debug(r.status_code)
        if r.status_code != requests.status_codes.codes.ok:
            logger.warning(r.json())
        
        return r

    def delete(self, action=None, params={}, data={}):
        if action is not None:
            self.api_action = action
        logger = logging.getLogger("OandaAPI.delete")
        self.api = "/".join([self.host, self.api_type, self.api_action])
        logger.debug(self.api)
        logger.debug(data)
        
        if self.account_id is not None:
            params["accountId"] = self.account_id
        r = requests.delete(self.api, headers={"Authorization": "Bearer "+self.api_token}, params=params, data=data)
        
        logger.debug(r.status_code)
        if r.status_code != requests.status_codes.codes.ok:
            logger.warning(r.json())
        
        return r

    def patch(self, action=None, params={}, data={}):
        if action is not None:
            self.api_action = action
        logger = logging.getLogger("OandaAPI.patch")
        self.api = "/".join([self.host, self.api_type, self.api_action])
        logger.debug(self.api)
        logger.debug(data)
        
        if self.account_id is not None:
            params["accountId"] = self.account_id
        r = requests.patch(self.api, headers={"Authorization": "Bearer "+self.api_token}, params=params, data=data)
        
        logger.debug(r.status_code)
        if r.status_code != requests.status_codes.codes.ok:
            logger.warning(r.json())
        
        return r
        