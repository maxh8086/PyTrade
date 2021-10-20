from alice_blue import *
from config import Credentials
import datetime
import time
from time import localtime,strftime
import pandas as pd
import threading
from orderClass import place_order



SCRIPT_LIST = ['SBIN', 'HDFC', 'IOC', 'CADILAHC', 'BATAINDIA',
               'ITC', 'DABUR', 'BIOCON', 'ESCORTS', 'LUPIN','LTI']
CDS_SCRIPT_LIST = ['USDINR FEB FUT']
MCX_SCRIPT_LIST = ['SILVERMIC FEB FUT', 'SILVERMIC APR FUT','CRUDEOIL FEB FUT','CRUDEOIL MAR FUT']


socket_opened = False
df = pd.DataFrame()
ORB_timeFrame = 60  # in seconds
ORB_df = pd.DataFrame()
TRADED_SCRIPT = []
def event_handler_quote_update(message):
    ltp = message['ltp']
    timestamp = datetime.datetime.fromtimestamp(message['exchange_time_stamp'])
    vol = message['volume']
    instrumnet = message['instrument'].symbol
    exchange = message['instrument'].exchange
    high = message['high']
    low = message['low']
    global df
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", localtime())
    df = df.append({'symbol': instrumnet, 'timestamp': timestamp, 'vol': vol,
                    'ltp': ltp, 'high': high, 'low': low ,'exchange' :exchange}, ignore_index=True)
    print(f"{instrumnet} {ltp} : {timestamp} : {vol} : {currentTime}")
    


def open_callback():
    global socket_opened
    socket_opened = True
    print("Socket opened")


def login():
    access_token = AliceBlue.login_and_get_access_token(username=Credentials.UserName.value, password=Credentials.PassWord.value, twoFA='a',
    api_secret=Credentials.SecretKey.value, app_id=Credentials.AppId.value)
   
    alice = AliceBlue(username=Credentials.UserName.value, password=Credentials.PassWord.value,
                      access_token=access_token, master_contracts_to_download=['MCX', 'NSE', 'CDS'])


    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)
   
    while(socket_opened == False):   
        pass
    for script in SCRIPT_LIST:
        alice.subscribe(alice.get_instrument_by_symbol('NSE', script), LiveFeedType.MARKET_DATA)
    for script in CDS_SCRIPT_LIST:
        alice.subscribe(alice.get_instrument_by_symbol('CDS', script), LiveFeedType.MARKET_DATA)
    for script in MCX_SCRIPT_LIST:
        alice.subscribe(alice.get_instrument_by_symbol(
            'MCX', script), LiveFeedType.MARKET_DATA)
    return alice
   
    


def createOHLC(alice,isFirstCandle):
    start = time.time()
    global df
    copydf = df.copy(deep=True).drop_duplicates()
    df = pd.DataFrame()
    if isFirstCandle:
        openHighForFisrtCandle(copydf)
    else : 
        getOHLC_df(copydf,alice)

    interval = ORB_timeFrame - (time.time() - start)
    print(f"Next check will start after {interval} sec : {datetime.datetime.now()}")
    threading.Timer(interval, createOHLC,args=[alice,False]).start()

def openHighForFisrtCandle(df):
    grouped = df.groupby('symbol')
    global ORB_df
    for name, group in grouped:
        group = group.sort_values('timestamp')
        timestamp =  group['timestamp'].iloc[0]
        symbol =  name
        high= group['high'].max()  
        low=  group['low'].min()
           
        data = {
            'timestamp': timestamp,
            'symbol': symbol,
            'high': high,
            'low':  low }
        ORB_df = ORB_df.append(data, ignore_index=True)
    ORB_df.set_index('symbol',inplace=True)
    print(ORB_df)



def getOHLC_df(df,alice):
    grouped = df.groupby('symbol')
    global TRADED_SCRIPT
    global ORB_df
    df_final = pd.DataFrame()
    for name, group in grouped:
        group = group.sort_values('timestamp')
        timestamp =  group['timestamp'].iloc[0]
        symbol =  name
        day_high= group['high'].iloc[0]
        day_low=group['low'].iloc[0]
        open= group['ltp'].iloc[0]
        close= group['ltp'].iloc[-1]
        high= group['ltp'].max()
        low=  group['ltp'].min()
        exchange = group['exchange'].iloc[0]
        try :
            if close > ORB_df.loc[symbol]['high'] and symbol not in TRADED_SCRIPT :
                print(f"Buy triggered at {datetime.datetime.now()} : {symbol} : {close}" )
                alice.placeBracketOrder(symbol,exchange,1,low,2*(high-low),close,TransactionType.Buy)
                TRADED_SCRIPT.append(symbol)
            elif close< ORB_df.loc[symbol]['low'] and symbol not in TRADED_SCRIPT:
                print(f"sell triggered at {datetime.datetime.now()} : {symbol} : {close}" )
                alice.placeBracketOrder(symbol,exchange,1,low,2*(high-low),close,TransactionType.Sell)
                TRADED_SCRIPT.append(symbol)
            data = {
                'timestamp': timestamp,
                'symbol': symbol,
                'day_high': day_high,
                'day_low': day_low,
                'open': open,
                'close': close,
                'high': high,
                'low':  low ,
                'orb_day_high':ORB_df.loc[symbol]['high'],
                'orb_day_low':ORB_df.loc[symbol]['low']}
            df_final = df_final.append(data, ignore_index=True)
        except Exception as e:
            print(e)
    print(df_final)
   
    


if __name__ == '__main__':
    alice = login()
    interval = ORB_timeFrame - datetime.datetime.now().second
    print("start in ", interval)
    time.sleep(interval)
    order = place_order(alice)
    createOHLC(order, True)
    
