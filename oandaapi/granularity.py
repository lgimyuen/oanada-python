# -*- coding: utf-8 -*-
import pandas as pd

def to_timedelta(granularity):
    time_delta = False
    if granularity == "M":
        time_delta = pd.Timedelta("1 month")
    elif granularity == "W":
        time_delta = pd.Timedelta("1 week")
    elif granularity[0] == "H":
        time_delta = pd.Timedelta("{0} hour".format(granularity[1:]))
    elif granularity[0] == "M":
        time_delta = pd.Timedelta("{0} minute".format(granularity[1:]))
    elif granularity[0] == "S":
        time_delta = pd.Timedelta("{0} second".format(granularity[1:]))
    
    return time_delta
        