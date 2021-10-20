from nsepython import *
from historicVolatility import get_vix
import os
import pandas as pd
# import xlwings as xw
from time import sleep
from datetime import datetime, time, timedelta
import json
import numpy as np


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)
df_list = []
mp_list = []
symbol = 'NIFTY'

oi_filename = os.path.join("../Files", "oi_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))
mp_filename = os.path.join("../Files", "mp_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))


r = option_chain(symbol)
ce_values = [data["CE"] for data in r['filtered']['data'] if "CE" in data]
pe_values = [data["PE"] for data in r['filtered']['data'] if "PE" in data]
ce_data = pd.DataFrame(ce_values)
pe_data = pd.DataFrame(pe_values)
ce_data = ce_data.sort_values(['strikePrice'])
pe_data = pe_data.sort_values(['strikePrice'])
oidata = pe_data.merge(ce_data, how='inner', on='strikePrice', suffixes=("_pe", "_ce"))
print(oidata)




# # c = mibian.BS([underlyingPrice, strikePrice, interestRate, daysToExpiration], volatility=volatility)
# interestRate = 10
# daysToExpiration = oidata['expiryDate_ce'] - date.today()
# # oidata["calldata_ce"] = c = mibian.BS([oidata['underlying_ce'], oidata['strikePrice'], interestRate, daysToExpiration], volatility=volatility)
# # oidata["putdata_pe"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["call_delta"] = oidata['strikePrice']*oidata['openInterest_ce']
# # oidata["put_delta"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["call_theta"] = oidata['strikePrice']*oidata['openInterest_ce']
# # oidata["put_theta"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["call_gama"] = oidata['strikePrice']*oidata['openInterest_ce']
# # oidata["put_gama"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["call_vega"] = oidata['strikePrice']*oidata['openInterest_ce']
# # oidata["put_vega"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["call_rho"] = oidata['strikePrice']*oidata['openInterest_ce']
# # oidata["put_rho"] = oidata['strikePrice']*oidata['openInterest_pe']
# # oidata["oi"] = oidata["calldata_ce"]+oidata["putdata_pe"]
# # print(oidata)
# maxpain = oidata.loc[oidata['oi'] == oidata["oi"].max()]['strikePrice'].values[0]
# # way of doing it to get only single value in int
# pcr = round(oidata['openInterest_pe'].sum() / oidata['openInterest_ce'].sum(), 2)
# call_decay = round(oidata.nlargest(5, 'openInterest_ce', keep='last')['change_ce'].mean(), 2)
# put_decay = round(oidata.nlargest(5, 'openInterest_pe', keep='last')['change_pe'].mean(), 2)
# ltp = oidata['underlyingValue_ce'].values[0]
