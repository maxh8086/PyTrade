from selenium import webdriver
import os
import requests
import pandas as pd
import xlwings as xw
from time import sleep
from datetime import datetime, time, timedelta
import json
import numpy as np


def get_session_cookies():
    currentdir = os.path.dirname(__file__)
    driverpath = os.path.join(currentdir, "chromedriver.exe").replace("\\", "/")
    if not os.path.exists(driverpath):
        print("Chrome Driver is missing from path {0}".format(driverpath))
    driver = webdriver.Chrome(executable_path=driverpath)
    driver.get("https://www.nseindia.com")
    print("Negotiating with server")
    cookies = driver.get_cookies()
    cookie_dict = {}
    with open("cookies", 'w') as line:
        for cookie in cookies:
            if cookie == "bm_sv":
                cookie_dict[cookie['name']] = cookie['value']
                line.write(json.dumps(cookie_dict))
    driver.quit()
    return cookie_dict

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)
wb = xw.Book(fullname="Option_chain_analysis.xlsx")  # this will create a new workbook
sheet_oi_single = wb.sheets("sheet1")
sheet_live = wb.sheets("sheet3")
sheet_oi_single.range('A2:M1500').api.Delete()
df_list = []
mp_list = []

oi_filename = os.path.join("../Files", "oi_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))
mp_filename = os.path.join("../Files", "mp_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))

url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
    'Upgrade-Insecure-Request': "1", "DNT": "1",
    'Accept-Language': 'en-IN,en; q=0.9, en-GB; q=0.8, en-US; q=0.7, mr; q=0.6, hi; q=0.5',
    'Accept-Encodong': 'gzip, deflate, br'}


def fetch_oi(df, mp_df):
    global df_list, mp_list
    tries = 1
    max_retries = 3
    while tries <= max_retries:
        try:
            session = requests.session()
            cookies = json.load(open('cookies').read())
            for cookie in cookies:
                if cookie == "bm_sv":
                    session.cookies.set(cookie, cookies[cookie])
            r = session.get(url, headers=headers, timeout=20).json()
            print("Captured data")
        except Exception as err:
            print("Error connecting to site, {0}".format(err))
            cookie_dict = get_session_cookies()
            for cookie in cookie_dict:
                if cookie == "bm_sv":
                    session.cookies.set(cookie, cookie_dict[cookie])
        try:
            r = session.get(url, headers=headers, timeout=25).json()
            print("Tring once again to captured data")
        except Exception as err:
            print("not getting data, {0}".format(err))
            tries +=1
            continue

        if 'filtered' not in r:
            tries +=1
            print("not getting data")

        ce_values = [data["CE"] for data in r['filtered']['data'] if "CE" in data]
        pe_values = [data["PE"] for data in r['filtered']['data'] if "PE" in data]
        ce_data = pd.DataFrame(ce_values)
        pe_data = pd.DataFrame(pe_values)
        ce_data = ce_data.sort_values(['strikePrice'])
        pe_data = pe_data.sort_values(['strikePrice'])
        print("Writing oi chain to excel")
        sheet_oi_single.range("A2").options(index=False, header=False).value = ce_data.drop(
            ['askPrice', 'askQty', 'bidQty', 'bidprice', 'expiryDate', 'identifier', 'totalBuyQuantity', 'totalSellQuantity',
             'underlyingValue', 'underlying'], axis=1)[['lastPrice', 'totalTradedVolume',
             'pchangeinOpenInterest', 'changeinOpenInterest','openInterest', 'impliedVolatility', 'strikePrice']]
        sheet_oi_single.range("G2").options(index=False, header=False).value = pe_data.drop(
            ['askPrice', 'askQty', 'bidQty', 'bidprice', 'expiryDate', 'identifier', 'totalBuyQuantity', 'totalSellQuantity',
             'underlyingValue', 'underlying'], axis=1)[['strikePrice', 'impliedVolatility','openInterest', 'changeinOpenInterest',
             'pchangeinOpenInterest', 'totalTradedVolume', 'lastPrice']]
        ce_data['type'] = "CE"
        pe_data['type'] = "PE"
        df1 = pd.concat([ce_data, pe_data])
        if len(df_list) > 0:
            df1['Time'] = df_list[-1][0]['Time']
        if len(df_list) > 0 and df1.to_dict('records') == df_list[-1]:
            print("Duplicate data, Not recording")
            sleep(10)
            tries +=1
            continue
        df1['Time'] = datetime.now().strftime("%H:%M")

        pcr = pe_data['totalTradedVolume'].sum()/ce_data['totalTradedVolume'].sum()

        mp_dict = {datetime.now().strftime("%H:%M"): {'underlying' : df1['underlyingValue'].iloc[-1],
                                                      'MaxPain': "0",
                                                      'PCR' : pcr,
                                                      'call_decay' : ce_data.nlargest(5,'openInterest', keep='last')['change'].mean(),
                                                      'put_decay' : pe_data.nlargest(5,'openInterest', keep='last')['change'].mean()}}
        df3 = pd.DataFrame(mp_dict).transpose()
        mp_df = pd.concat([mp_df, df3])
        print("Writing max pain to excel")
        wb.sheets('Sheet2').range("A1").options(header = True).value = mp_df
        with open(mp_filename, "w") as files:
            files.write(json.dumps(mp_df.to_dict(), indent=4, sort_keys=True))
        if not df.empty:
            df = df[
                    ['strikePrice', 'expiryDate', 'underlying', 'identifier', 'openInterest', 'changeinOpenInterest',
                     'pchangeinOpenInterest','totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change', 'pChange',
                     'totalBuyQuantity', 'totalSellQuantity', 'bidQty', 'bidprice', 'askQty','askPrice','underlyingValue',
                     'type','Time']]
        df1 = df1[['strikePrice', 'expiryDate', 'underlying', 'identifier', 'openInterest', 'changeinOpenInterest',
                     'pchangeinOpenInterest','totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change', 'pChange',
                     'totalBuyQuantity', 'totalSellQuantity', 'bidQty', 'bidprice', 'askQty','askPrice','underlyingValue',
                     'type','Time']]
        df = pd.concat([df, df1])
        df_list.append(df1.to_dict('records'))
        with open(oi_filename, "w") as files:
            files.write(json.dumps(df_list, indent=4, sort_keys=True))
        return df, mp_df

    if tries >= max_retries:
        print("max retries exceeded, no new data at {0}".format(datetime.now()))
        return df, mp_df


def main():
    try:
        df_list = json.loads(open(oi_filename).read())
    except Exception as error:
        print("Error reading oi data from json file, Error {0}".format(error))
        df_list = []
    if df_list:
        df = pd.DataFrame()
        for item in df_list:
            df = pd.concat([df, pd.DataFrame(item)])
    else:
        df = pd.DataFrame()

    try:
        mp_list = json.loads(open(mp_filename).read())
        mp_df = pd.DataFrame().from_dict(mp_list)
    except Exception as error:
        print("Error reading maxpain data from json file, Error {0}".format(error))
        mp_list = []
        mp_df = pd.DataFrame()
    # ### To restrict loop in specific / Market time window
    # timeframe = 5
    # while time(9,15) <= datetime.now().time() <= time(15,30):
    #     timenow = datetime.now()
    #     check = True if timenow.minute/timeframe in list(np.arange(0.0, 12.0)) else False
    #     if check:
    #         nextscan = timenow + timedelta(minutes=timeframe)
    #         df, mp_df = fetch_oi(df, mp_df)
    #         if not df.empty:
    #             df['impliedVolatility'] = df['impliedVolatility'].replace(to_replace=0, method='bfill').values
    #             df['identifier'] = df['strikePrice'].astype(str) + df['type']
    #             sheet_live.range("A1").value = df
    #             wb.api.RefreshAll()
    #             waitsecs = int((nextscan - datetime.now()).seconds)
    #             print("wait for {0} Seconds for next scan".format(waitsecs))
    #             sleep(waitsecs) if waitsecs > 0 else sleep(0)
    #         else:
    #             print("No Data Received")
    #             sleep(30)

    ### code without time loop starts below ###
    df, mp_df = fetch_oi(df, mp_df)
    if not df.empty:
        df['impliedVolatility'] = df['impliedVolatility'].replace(to_replace=0, method='bfill').values
        df['identifier'] = df['strikePrice'].astype(str) + df['type']
        sheet_live.range("A1").value = df
        wb.api.RefreshAll()
    else:
        print("No Data Received")
        sleep(30)

if __name__ == '__main__':
    main()
