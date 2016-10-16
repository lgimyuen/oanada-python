from oandaapi.api import API
class Instrument(API):
        
        """
            instruments ~ tuple of instrument string
            fields ~ tuple of fields string
        """
        def get_instruments(self, instruments=None, fields=None):        
            params = {}
            
            if instruments is not None:
                params["instruments"] = ",".join(instruments)
            
            if fields is not None:
                params["fields"] = ",".join(fields)
                
            r = self.get(action="instruments", params=params)
            return (r.json(), r.status_code)