import pymysql
import sqlalchemy as db
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
%matplotlib inline
engine = db.create_engine('mysql+pymysql://root:root@127.0.0.1:3306/market_data')  #change parameter as per your Database config

def getTable(strike_price,table_name,expirydate):
    
    table_df = pd.read_sql_table(table_name,con=engine)
    if expirydate is not None :
        table_df = table_df[table_df['Exp. Date'] == expirydate]
    if len(strike_price) > 0 :
        table_df = table_df[table_df['Strike Price'].isin(strike_price)]
    grouped = table_df.groupby(['Time']).agg({'LTP':'sum','OI':'sum','No.of contracts':'sum','OI Change':'sum','IV':'sum'}).reset_index()
    return grouped



pe_strike_price = [14000,14100]  #select strike for PE
ce_strike_price = [14000,14100]  #select strike for CE
expirydate = '2021-01-07'        #edit expiry date 
table_ce= getTable(ce_strike_price,'oc_ce',expirydate)
table_pe= getTable(pe_strike_price,'oc_pe',expirydate)
final = pd.merge(table_pe,table_ce,how='left', on=['Time'],suffixes = ("_PE", "_CE"))




fig, axes = plt.subplots(nrows=2, ncols=2,figsize = (20,12))
ax2 = axes[0,0].twinx()
final.plot(kind='line',x='Time',y='OI_PE', ax=axes[0,0],grid = True,style='g')
final.plot(kind='line',x='Time',y='OI_CE', ax=ax2,grid = True,style='r')

ax2 = axes[0,1].twinx()
final.plot(kind='line',x='Time',y='IV_PE', ax=axes[0,1],grid = True,style='g')
final.plot(kind='line',x='Time',y='IV_CE', ax=ax2,grid = True,style='r')

ax2 = axes[1,0].twinx()
final.plot(kind='line',x='Time',y='LTP_PE', ax=axes[1,0],grid = True,style='g')
final.plot(kind='line',x='Time',y='LTP_CE', ax=ax2,grid = True,style='r')

ax2 = axes[1,1].twinx()
final.plot(kind='line',x='Time',y='OI Change_PE', ax=axes[1,1],grid = True,style='g')
final.plot(kind='line',x='Time',y='OI Change_CE', ax=ax2,grid = True,style='r')
#plt.savefig('pic.png')
print(final.iloc[-1].Time)
plt.show()
