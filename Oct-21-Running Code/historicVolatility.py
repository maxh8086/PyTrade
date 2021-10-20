import pandas as pd
import numpy as np
import requests
import os
import math
import csv
import re
from datetime import date, timedelta
from bs4 import BeautifulSoup

# import logging
# logging.basicConfig(level='CRITICAL')
# logging.basicConfig(level='WARNING')
# logging.basicConfig(level=logging.WARNING)

# set date range for historical prices
end_date = date.today()  # 24-03-2021
start_date = end_date - timedelta(days=364)  # 24-03-2020

# reformat date range
end = end_date.strftime('%d-%m-%Y')
start = start_date.strftime('%d-%m-%Y')


def pct_change(first, second):
    diff = second - first
    change = 0
    try:
        if diff > 0:
            change = (diff / first) * 100
        elif diff < 0:
            diff = first - second
            change = -((diff / first) * 100)
    except ZeroDivisionError:
        return float('inf')
    return change

def url_to_json(url):
    baseurl = "https://www.nseindia.com"
    newheader = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    }

    try:
        output = requests.get(baseurl, headers=newheader)
        s = requests.Session()
        output = s.get(baseurl, headers=newheader)
        output = s.get(url, headers=newheader).json()
    except ValueError:
        print(output, "error")
    return output


def old_url_raw(url):
    baseurl = "https://www.nseindia.com"

    oldheader = {
        "Host": "www1.nseindia.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www1.nseindia.com/products/content/equities/indices/historical_index_data.htm",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With",
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

    try:
        output = requests.get(baseurl, headers=oldheader)
        s = requests.Session()
        output = s.get(baseurl, headers=oldheader)
        output = s.get(url, headers=oldheader)
    except ValueError:
        print(output, "error")
    return output


def new_url_raw(url):
    baseurl = "https://www.nseindia.com"

    newheaders = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    }

    try:
        output = requests.get(baseurl, headers=newheaders)
        s = requests.Session()
        output = s.get(baseurl, headers=newheaders)
        output = s.get(url, headers=newheaders)
    except ValueError:
        print(output, "error")
    return output


def get_indices_hv(indices):
    prices = ''
    indicsurl = "https://www1.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType=" + indices + "&fromDate=" + start + "&toDate=" + end

    while True:
        result = pd.DataFrame()
        response = old_url_raw(indicsurl)
        if response.status_code == 200:
            page_content = BeautifulSoup(response.content, "html.parser")
            try:
                a = page_content.find(id="csvContentDiv").get_text()
                a = a.replace(':', ", \n")
                with open("data.csv", "w") as f:
                    f.write(a)
                df = pd.read_csv("data.csv", usecols=['Date', 'Close'])
                result = pd.concat([result, df])
                # transform json file to dataframe
                prices = pd.DataFrame(result)
            except AttributeError:
                break
        else:
            response.raise_for_status()
        break

    try:
        os.remove("data.csv")
    except OSError:
        pass

    return prices


def get_stk_hv(symbol):
    prices = ''
    baseurl = "https://www.nseindia.com"
    series = 'EQ'
    extendedlink = "/api/historical/cm/equity" + "?symbol=" + symbol + "&series=[%22" + series + "%22]&from=" + start + "&to=" + end + "&csv=true"
    stkurl = baseurl + extendedlink

    while True:
        response = new_url_raw(stkurl)
        if response.status_code == 200:
            data = response.content.decode('utf-8').splitlines()
            try:
                # Open the file for writing
                with open("stock_data.csv", "w", encoding='utf-8') as csv_file:
                    # Create the writer object with tab delimiter
                    writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_NONE, quotechar='', escapechar='\\')
                    for line in data:
                        writer.writerow(re.split('\s+', line))
                df = pd.read_csv("stock_data.csv", delimiter=',', quotechar='"', escapechar='\\',
                                 usecols=['Date,\\', 'close,\\'])
                df['Date'] = df['Date,\\']
                df['Date'] = df.Date.str.replace("\\", "")
                df['Close'] = df['close,\\']
                df['Close'] = df.Close.str.replace("\\", "").astype(float)
                prices = df.drop(['Date,\\', 'close,\\'], axis=1)
            except AttributeError:
                break
        else:
            response.raise_for_status()
        break
    try:
        os.remove("stock_data.csv")
    except OSError:
        pass
    return prices


def get_vix(symbol):
    if symbol == 'NIFTY':
        indices = 'NIFTY 50'
        prices = get_indices_hv(indices)
    elif symbol == 'BANKNIFTY':
        indices = 'NIFTY BANK'
        prices = get_indices_hv(indices)
    else:
        prices = get_stk_hv(symbol)

    # sort dates in descending order
    prices['Date'] = pd.to_datetime(prices['Date'])
    prices.sort_values(by=['Date'], inplace=True, ascending=True)

    # calculate daily logarithmic return
    prices['returns'] = (np.log(prices.Close / prices.Close.shift(-1)))

    # calculate daily standard deviation of returns
    # NumPy's std calculates the population standard deviation by default (it is behaving like Excel's STDEVP).
    # To make NumPy's std function behave like Excel's STDEV, pass in the value ddof=1:
    d_std = np.std(prices.returns, ddof=1)

    # annualized daily standard deviation
    samples = len(prices.index) - 1
    w_vix = d_std * math.sqrt(6)
    m_vix = d_std * math.sqrt(31)
    vix = d_std * math.sqrt(samples)
    d_vix_pc = np.round(d_std * 100, 2)
    w_vix_pc = np.round(w_vix * 100, 2)
    m_vix_pc = np.round(m_vix * 100, 2)
    y_vix_pc = np.round(vix * 100, 2)
    return d_vix_pc, w_vix_pc, m_vix_pc, y_vix_pc


def get_symbol_open_data(symbol):
    if symbol == 'NIFTY':
        indics = 'NIFTY 50'
    elif symbol == 'BANKNIFTY':
        indics = 'NIFTY BANK'
    else:
        indics = symbol

    indicsOHLCurl = "https://www.nseindia.com/api/equity-stockIndices?index=" + indics
    json_data = url_to_json(indicsOHLCurl)
    # print(json_data)
    result = [i for i in json_data['data'] if indics in i['symbol']]
    opench = pct_change(result[0]['open'], result[0]['previousClose'])
    return result[0]['open'], result[0]['previousClose'], opench
    # return 32900, 32783, 0.9


# dayopen, prevclose, pchange = get_symbol_open_data(symbol)

# print(get_symbol_open_data('BANKNIFTY'))