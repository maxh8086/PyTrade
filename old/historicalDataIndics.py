from datetime import date, timedelta
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import os
import math
import logging
logging.basicConfig(level='CRITICAL')

def get_indices_hv(symbol):
    oldHeader = {
        "Host" : "www1.nseindia.com",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
        "Accept" : "*/*",
        "Accept-Language" : "en-US,en;q=0.5",
        "Accept-Encoding" : "gzip, deflate, br",
        "X-Requested-With" : "XMLHttpRequest",
        "Referer" : "https://www1.nseindia.com/products/content/equities/indices/historical_index_data.htm",
        "Access-Control-Allow-Origin" : "*",
        "Access-Control-Allow-Methods" : "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers" : "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With",
        'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    if symbol=='NIFTY':
        indics = 'NIFTY 50'
    elif symbol=='BANKNIFTY':
        indics = 'NIFTY BANK'

    # set date range for historical prices
    end_date = date.today()  # 24-03-2021
    start_date = end_date - timedelta(days=364)  # 24-03-2020

    # reformat date range
    end = end_date.strftime('%d-%m-%Y')
    start = start_date.strftime('%d-%m-%Y')

    indicsurl = "https://www1.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType=" + indics + "&fromDate=" + start + "&toDate=" + end

    while (True) :
        result = pd.DataFrame()
        response = []
        response = requests.get(indicsurl, headers=oldHeader)
        if (response.status_code == requests.codes.ok) :
            page_content = BeautifulSoup(response.content, "html.parser")
            try :
                a = page_content.find(id="csvContentDiv").get_text();
                a = a.replace(':', ", \n")
                with open("data.csv", "w") as f :
                    f.write(a)
                df = pd.read_csv("data.csv", usecols=['Date', 'Close'])
                result = pd.concat([result, df])
            except AttributeError :
                break;
        else :
            response.raise_for_status()
        break;

    try :
        os.remove("data.csv")
    except(OSError) :
        pass

    # transform json file to dataframe
    prices = pd.DataFrame(result)

    # sort dates in descending order
    prices['Date'] = pd.to_datetime(prices['Date'])
    prices.sort_values(by=['Date'], inplace=True, ascending=True)

    # calculate daily logarithmic return
    prices['returns'] = (np.log(prices.Close / prices.Close.shift(-1)))

    # calculate daily standard deviation of returns
    # NumPy's std calculates the population standard deviation by default (it is behaving like Excel's STDEVP).
    # To make NumPy's std function behave like Excel's STDEV, pass in the value ddof=1:
    daily_std = round(np.std(prices.returns, ddof=1), 6)

    # annualized daily standard deviation
    samples = len(prices.index) - 1
    std = daily_std * round(math.sqrt(samples), 4)
    vix = np.round(std * 100, 2)
    return vix
