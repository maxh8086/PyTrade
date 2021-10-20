# Importing Third Party Library for NSE
from nsepython import option_chain
import mibian

# Import In house Library for NSE
from historicVolatility import get_vix, get_symbol_open_data

# Import Python Library
import os
import sys
import pandas as pd
from time import sleep
from datetime import datetime, time, timedelta, date
import json
import numpy as np
import math

# import gspread
# import gspread_dataframe as gd

# import logging
# import logging
# logging.basicConfig(level='WARNING')
# logging.basicConfig(level=logging.WARNING)


# initializing variable
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)

oi_filename = os.path.join("Files", "oi_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))
mp_filename = os.path.join("Files", "mp_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))
print(oi_filename)
try:
    df_file = json.loads(open(oi_filename).read())
    df_read = pd.DataFrame().from_dict(df_file)
    print(df_read)
except Exception as error:
    print("Error reading oi data from json file, Error {0}".format(error))
    df_read = pd.DataFrame()
# try:
#     mplist = json.loads(open(mp_filename).read())
#     mp_df = pd.DataFrame().from_dict(mplist)
# except Exception as error:
#     print("Error reading maxpain data from json file, Error {0}".format(error))
#     mp_df = pd.DataFrame()