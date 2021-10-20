import requests
import pandas as pd
import time 
from datetime import datetime, timedelta
from datetime import date

start_date = date(2020,4,15)   #yyyy-mm-dd format
end_date =  date(2021,4,15)     #yyyy-mm-dd format

userid = 'POIU788'
timeframe= 'minute'
ciqrandom = '161746886774'

auth_token = 'enctoken pyPXxogbJOEjzwgWsq1GsXj7ZhEdjdjjdd9pjldJT+gjaR1d7GtHoci5G6crt2qsqmHpZicTdnBLw=='
headers = {'Authorization': auth_token}



start = time.time()
token_df = pd.read_excel(r'F:\demo_file\token_symbol.xlsx')
for i in range(0,len(token_df)):
    start1 = time.time()
    token = token_df.loc[i]['TOKEN']
    columns = ['timestamp','Open','High','Low','Close','V','OI']
    final_df = pd.DataFrame(columns=columns)
    from_date = start_date
   
    while from_date < end_date :
    
        to_date =  from_date + timedelta(days=30)
        url = f'https://kite.zerodha.com/oms/instruments/historical/{token}/{timeframe}?user_id={userid}&oi=1&from={from_date}&to={to_date}&ciqrandom={ciqrandom}'
        resJson = requests.get(url, headers=headers).json()
        candelinfo = resJson['data']['candles']
        df= pd.DataFrame(candelinfo, columns=columns)
        
        final_df = final_df.append(df,ignore_index=True)
        from_date = from_date + timedelta(days=31)
        
    
    final_df['timestamp'] = pd.to_datetime(final_df['timestamp'],format = '%Y-%m-%dT') 
    final_df['date'] = pd.to_datetime(final_df['timestamp']).dt.date
    final_df['time'] = pd.to_datetime(final_df['timestamp']).dt.strftime('%H:%M')
    final_df['ticker'] = token_df.loc[i]['SYMBOL']
    final_df.drop('timestamp',axis = 1,inplace = True)
    final_df = final_df[['ticker','date','Open','High','Low','Close','V','OI','time']]
    
    filename = str(token_df.loc[i]['SYMBOL']) +'.txt'
    final_df.to_csv('F:/demo_file/' + filename, header =False,index = False )
    print(time.time() - start1)
    print(final_df)
print(time.time() - start)