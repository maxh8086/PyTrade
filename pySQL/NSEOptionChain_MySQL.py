# Import Python Library
import sys
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta

import time
from time import sleep

import pandas as pd
import numpy as np
from numpy import log
import math

# # WARNING: All numbers should be floats -> x = 1.0
from py_vollib_vectorized import price_dataframe, get_all_greeks
from py_vollib_vectorized import vectorized_implied_volatility as iv
from math import e

import requests
from io import StringIO
from bs4 import BeautifulSoup

import pymysql
import sqlalchemy
from sqlalchemy import Table, Column, Float, Integer, String, MetaData, ForeignKey

# Import In house Library for NSE
from historicVolatility import get_vix, get_symbol_open_data

# init all necessary variables
today = date.today()
symbol = 'BANKNIFTY'
indices = 'NIFTY BANK'
table = symbol.lower()
EOD_DB_UPDATED = 0
BOD_DB_UPDATED = 0

# connect mySQL DB using sqlalchemy
engine = sqlalchemy.create_engine('mysql+pymysql://pyadmin:pyU$er#123@127.0.0.1:3306/eod_data')
wpdb = sqlalchemy.create_engine('mysql+pymysql://pyadmin:pyU$er#123@127.0.0.1:3306/spwpdb')

# # Connect mySQL DB using pymySQL coonector
# pyconnector = pymysql.connect(host='127.0.0.1', user='pyadmin', password = "pyU$er#123", db='eod_data',)

# set date range for historical prices
start_of_year = date(today.year, 1, 1)
end_date = today  # - timedelta(days=400) # 24-03-2021
start_date = end_date - timedelta(days=30)  # 24-03-2020

# reformat date range
def_end = end_date.strftime('%d-%b-%Y')
def_start = start_date.strftime('%d-%b-%Y')


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


def percentage_change(col1, col2):
    return round(((col2 - col1) / col1) * 100, 2)


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
    except ValueError as error:
        print(error, "error")
        return
    finally:
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
    # except ValueError:
    except ValueError as error:
        print(error, "error")
        return
    finally:
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
    except ValueError as error:
        print(error, "error")
        return
    except HTTPError as error:
        print("Server not reachable try again after sometime")
        return
    finally:
        return output


def option_chain(symbol):
    URL = 'https://www.nseindia.com/api/option-chain-indices?symbol=' + symbol
    response = url_to_json(URL)
    return response


def get_online_db(indices=indices, sdt=def_start, edt=def_end):
    indicsurl = "https://www1.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType=" + indices + "&fromDate=" + sdt + "&toDate=" + edt
    while True:
        try:
            response = old_url_raw(indicsurl)
        except exception:
            print('unable to update historical data')
            return
        finally:
            if response.status_code == 200:
                page_content = BeautifulSoup(response.content, "html.parser")
                try:
                    strings = page_content.find(id="csvContentDiv").get_text().replace(':', "\n")
                    strings = strings.replace(' ', '')
                    pdfo = pd.read_csv(StringIO(strings), header=0)
                    pdfo['Open'] = pdfo['Open'].replace('-', np.nan).fillna(pdfo.Close).astype(float).round(2)
                    pdfo['High'] = pdfo['High'].replace('-', np.nan).fillna(pdfo.Close).astype(float).round(2)
                    pdfo['Low'] = pdfo['Low'].replace('-', np.nan).fillna(pdfo.Close).astype(float).round(2)
                    pdfo['SharesTraded'] = pdfo['SharesTraded'].replace('-', '0')
                    pdfo['Turnover(Rs.Cr)'] = pdfo['Turnover(Rs.Cr)'].replace('-', '0')
                    pdfo['Date'] = pd.to_datetime(pdfo['Date']).dt.strftime('%Y-%m-%d').astype(str)
                    # print(df)
                except AttributeError as e:
                    return
            else:
                response.raise_for_status()
        break
    return pdfo


def get_db(table=table, std=def_start, edt=def_end, update=None):
    if table != "bod_data":
        # init required variables
        df = pd.DataFrame()
        if update is None:
            std = datetime.strptime(std, '%d-%b-%Y').strftime('%Y-%m-%d')
            etd = datetime.strptime(edt, '%d-%b-%Y').strftime('%Y-%m-%d')
            myQuery = '''
                     SELECT * 
                     FROM {0} 
                     WHERE Date BETWEEN '{1}' AND '{2}' 
                     ORDER BY Date DESC
                     ;'''.format(table, std, etd)
        elif update == 'lastline':
            myQuery = '''
                     SELECT * 
                     FROM {0}
                     ORDER BY Date DESC
                     Limit 1
                     ;'''.format(table)
        else:
            myQuery = '''SELECT * FROM {0};'''.format(table)

        try:
            df = pd.read_sql_query(myQuery, engine, coerce_float=False)
        finally:
            return df
    else:
        # init required variables
        df = pd.DataFrame()
        myQuery = '''SELECT * FROM {0};'''.format(table)
        try:
            df = pd.read_sql_query(myQuery, engine, coerce_float=False)
        finally:
            return df


def df_to_sql(df, table, db):
    # To connect MySQL database
    # Connect mySQL DB using pymySQL coonector
    pyconnector = pymysql.connect(host='127.0.0.1', user='pyadmin', password="pyU$er#123", db='eod_data', )

    cursor = pyconnector.cursor()
    updatequery = ('''
                   ALTER TABLE {0}
                   CHANGE COLUMN `Date` `Date` DATE NOT NULL ,
                   ADD PRIMARY KEY (`Date`),
                   ADD UNIQUE INDEX `Date_UNIQUE` (`Date` ASC) VISIBLE;
                   ''').format(table)

    if db == "eod_data":
        try:
            # print(df)
            df.to_sql(name=table, con=engine, index=False, if_exists='replace',
                      dtype={'Date': sqlalchemy.Date(),
                             'Open': sqlalchemy.types.Float(),
                             'High': sqlalchemy.types.Float(),
                             'Low': sqlalchemy.types.Float(),
                             'Close': sqlalchemy.types.Float(),
                             'NaturalLog': sqlalchemy.types.Float(),
                             'StdDev': sqlalchemy.types.Float(),
                             'W_HV': sqlalchemy.types.Float(),
                             'M_HV': sqlalchemy.types.Float(),
                             'Y_HV': sqlalchemy.types.Float(),
                             'SharesTraded': sqlalchemy.types.Float(),
                             'Turnover(Rs.Cr)': sqlalchemy.types.Float()
                             })

            # Update  / alter Database Schema to default
            cursor.execute(updatequery)
            output = pyconnector.commit()
            print('Backfill completed(DF to SQL)')

        finally:
            # To close the connection
            cursor.close()
            pyconnector.close()
    elif db == "bod_data":
        try:
            df.to_sql(name=table, con=engine, index=False, if_exists='replace',
                      dtype={'Date': sqlalchemy.Date(),
                             'symbol': sqlalchemy.types.VARCHAR(20),
                             'Open': sqlalchemy.types.Float(precision=2),
                             'previousClose': sqlalchemy.types.Float(precision=2),
                             'pChange': sqlalchemy.types.Float(precision=2)})
        finally:
            print('BOD Data Updated')


def update_db(table=table, indices=indices, std=def_start, edt=def_end):
    # get online data to process and update
    try:
        online = get_online_db(indices, std, edt)
    except exception:
        print('issue while fetching online data')
        online = pd.DataFrame()
        return online
    finally:
        # get offline data to process and update
        offline = get_db(table, None, None, True)

        merged = pd.concat([online, offline])
        merged['Date'] = pd.to_datetime(merged['Date']).dt.strftime('%Y-%m-%d').astype(str)
        merged = merged.drop_duplicates(subset=['Date'])
        merged = merged.sort_values(by='Date', ascending=True)
        merged['NaturalLog'] = merged['NaturalLog'].fillna(0).astype(float).round(6)
        merged['StdDev'] = merged['StdDev'].fillna(0).astype(float).round(6)
        merged['W_HV'] = merged['W_HV'].fillna(0).astype(float).round(6)
        merged['M_HV'] = merged['M_HV'].fillna(0).astype(float).round(6)
        merged['Y_HV'] = merged['Y_HV'].fillna(0).astype(float).round(6)
        merged['NaturalLog'] = np.log(merged.Close / merged.Close.shift(-1)).shift(1)
        merged['StdDev'] = merged['NaturalLog'].rolling(252).std().fillna(0).astype(float).round(6)
        merged['W_HV'] = round(merged['StdDev'] * math.sqrt(5), 2)
        merged['M_HV'] = round(merged['StdDev'] * math.sqrt(22), 2)
        merged['Y_HV'] = round(merged['StdDev'] * math.sqrt(252), 2)
        # print(merged.tail(50))

        # Update data to DB
        df_to_sql(merged, table, 'eod_data')


def eod_backfill(indices, table=table):
    # Initialize required variables
    prices = pd.DataFrame()
    inityear = 2000
    initdate = date(inityear, 1, 1)
    year_range = relativedelta(today, initdate)

    for i in range(year_range.years):
        st1 = (date(inityear, 1, 1) + relativedelta(years=i)).strftime("%d-%m-%Y")
        ed1 = (date(inityear, 11, 30) + relativedelta(years=i)).strftime("%d-%m-%Y")
        prices = prices.append(get_online_db(indices, st1, ed1))
        st2 = (date(inityear, 12, 1) + relativedelta(years=i)).strftime("%d-%m-%Y")
        ed2 = (date(inityear, 12, 31) + relativedelta(years=i)).strftime("%d-%m-%Y")
        prices = prices.append(get_online_db(indices, st2, ed2))
        print('initiating backfill for period:', st1, ' to ', ed2)
    st3 = date(today.year, 1, 1).strftime("%d-%m-%Y")
    ed3 = today.strftime("%d-%m-%Y")
    print('initiating backfill for period:', st3, ' to ', ed3)
    prices = prices.append(get_online_db(indices, st3, ed3))
    # print(prices)
    prices ['Date'] = pd.to_datetime(prices ['Date']).dt.strftime('%Y-%m-%d').astype(str)
    prices = prices.drop_duplicates(subset=['Date'])
    prices ['NaturalLog'] = np.log(prices.Close / prices.Close.shift(-1)).shift(1).fillna(0).astype(float).round(6)
    prices ['StdDev'] = prices ['NaturalLog'].rolling(252).std().fillna(0).astype(float).round(6)
    prices ['W_HV'] = round(prices ['StdDev'] * math.sqrt(5) * 100, 2)
    prices ['M_HV'] = round(prices ['StdDev'] * math.sqrt(22) * 100, 2)
    prices ['Y_HV'] = round(prices ['StdDev'] * math.sqrt(252) * 100, 2)
    df_to_sql(prices, table, 'eod_data')


def drop_table(table):
    print('need to drop table {}'.format(table))
    # Connect mySQL DB using pymySQL coonector
    pyconnector = pymysql.connect(host='127.0.0.1', user='pyadmin', password="pyU$er#123", db='eod_data', )
    cursor = pyconnector.cursor()
    dropquery = ('''DROP TABLE IF EXISTS {0} ;''').format(table)
    output = cursor.execute(dropquery)
    # To close the connection
    cursor.close()
    pyconnector.close()
    return output


def request_eod(table):
    print('checking for eod data')
    output = ''
    pyconnector = pymysql.connect(host='127.0.0.1', user='pyadmin', password="pyU$er#123", db='eod_data', )
    cursor1 = pyconnector.cursor()
    cursor2 = pyconnector.cursor()
    queryrow = 'SELECT COUNT(*) FROM {0};'.format(table)
    updatequery = ('''SELECT * FROM {0} ORDER BY Date DESC Limit 1;''').format(table)
    try:
        # Connect mySQL DB using pymySQL coonector
        cursor1.execute(updatequery)
        output = cursor1.fetchone()
        cursor2.execute(queryrow)
        rowcount = cursor2.fetchall() [0] [0]
    except pymysql.ProgrammingError as e:
        if (e.args [0] == 1146):
            print("Table dosen't exist, need to backfill")
            output = None
    finally:
        # To close the connection
        cursor1.close()
        cursor2.close()
        pyconnector.close()

        if output is None:
            print('initiated complete backfill')
            eod_backfill(indices, table)
        elif output [0] < start_of_year:
            print('Dropped old table and initiated complete backfill')
            drop_table(table)
            eod_backfill(indices, table)
        elif output [0] <= (today - timedelta(days=30)) and output [0] >= start_of_year:
            print('initiated full year backfill')
            beganing_year = start_of_year.strftime('%d-%m-%Y')
            update_db(table, indices, beganing_year, def_end)
        elif 0 < today.weekday() < 5 and output [0] != today and rowcount > 252:
            print('initiated backfill for weekdays')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 5 and output [0] != (today - timedelta(days=1)) and rowcount > 252:
            print('initiated backfill over weekend')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 6 and output [0] != (today - timedelta(days=2)) and rowcount > 252:
            print('initiated backfill over weekend')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 0 and output [0] != (today - timedelta(days=3)) and rowcount > 252:
            print('initiated for weekend')
            update_db(table, indices, def_start, def_end)
        else:
            return get_db(table, update='lastline').iloc [0]

    return get_db(table, update='lastline').iloc [0]


def get_bod_online():
    table = "bod_data"
    indicsOHLCurl = "https://www.nseindia.com/api/equity-stockIndices?index=" + indices
    json_data = url_to_json(indicsOHLCurl)
    # print(json_data)
    result = [i for i in json_data ['data'] if indices in i ['symbol']]
    bod_df = pd.DataFrame(json_data ['data'], columns=['symbol', 'open', 'previousClose'])
    bod_df.insert(loc=0, column='Date', value=today)
    bod_df ['pChange'] = percentage_change(bod_df ['previousClose'], bod_df ['open'])
    df_to_sql(bod_df, table, table)
    return 1


def request_bod():
    print('fetching BOD data')
    output = ''
    table = "bod_data"
    pyconnector = pymysql.connect(host='127.0.0.1', user='pyadmin', password="pyU$er#123", db='eod_data', )
    cursor = pyconnector.cursor()
    updatequery = ('''SELECT * FROM {0};''').format(table)
    try:
        # Connect mySQL DB using pymySQL coonector
        cursor.execute(updatequery)
        output = cursor.fetchone()
    except pymysql.ProgrammingError as e:
        if (e.args [0] == 1146):
            print("Table dosen't exist, need to backfill")
            output = None
    finally:
        # To close the connection
        cursor.close()
        pyconnector.close()

        if output is None:
            print('checking bod online')
            get_bod_online()
            return get_db(table)
        elif output [0] != today and today.weekday() < 5:
            print('updating bod for today')
            get_bod_online()
            return get_db(table)
        elif output [0] == today or today.weekday() >= 5:
            return get_db(table)


def nearest(datelist, pivot=today):
    items = [datetime.strptime(d, '%d-%b-%Y').date() for d in datelist]
    return min(items, key=lambda x: abs(x - pivot)).strftime('%d-%b-%Y')


def get_nearest(strike_data, lastprice):
    price_array = []
    first_ce = 0
    first_pe = 0
    second_ce = 0
    second_pe = 0
    for i in strike_data:
        price_array.append([round(abs(lastprice - i), 2), i])
    strike_list = sorted(price_array)
    if strike_list[0][1] > lastprice:
        first_ce = strike_list[0][1]
        first_pe = strike_list[1][1]
    if strike_list[1][1] > lastprice:
        first_ce = strike_list[1][1]
        first_pe = strike_list[0][1]
    if strike_list[2][1] > lastprice:
        second_ce = strike_list[2][1]
        second_pe = strike_list[3][1]
    if strike_list[3][1] > lastprice:
        second_ce = strike_list[3][1]
        second_pe = strike_list[2][1]
    return first_ce, first_pe, second_ce, second_pe


def total_loss_at_strike(chain, expiry_price):
    # """Calculate loss at strike price"""
    # All call options with strike price below the expiry price will result in loss for option writers
    in_money_calls = chain[chain['strikePrice'] < expiry_price][["oI_ce", "strikePrice"]]
    in_money_calls["CE loss"] = (expiry_price - in_money_calls['strikePrice']) * in_money_calls["oI_ce"]

    # All put options with strike price above the expiry price will result in loss for option writers
    in_money_puts = chain[chain['strikePrice'] > expiry_price][["oI_pe", "strikePrice"]]
    in_money_puts["PE loss"] = (in_money_puts['strikePrice'] - expiry_price) * in_money_puts["oI_pe"]
    total_loss = in_money_calls["CE loss"].sum() + in_money_puts["PE loss"].sum()
    return total_loss


def geeks_calc(oiraw):
    geeks_list = []
    int_rate = float(10 /100)
    oiraw['expiryDate'] = pd.to_datetime(oiraw['expiryDate'], format =  '%d-%b-%Y')
    # print(underlaying,expiry,strike,itype,ltp)
    FMT = '%H:%M:%S'
    s1 = datetime.now().strftime(FMT)
    s2 = '15:30:00'  # Expiry End
    tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
    timeleft = (tdelta.seconds / 86400)
    oiraw['tte'] = ((oiraw['expiryDate']-pd.Timestamp(date.today())).dt.days + timeleft) / 365
    oiraw['int'] = int_rate
    oiraw['underlyingValue'] = oiraw['underlyingValue'].astype(float)
    oiraw['strikePrice'] = oiraw['strikePrice'].astype(float)
    oiraw['ltP'] = oiraw['ltP'].astype(float)
    oiraw['tte'] = oiraw['tte'].astype(float)
    oiraw['Flag'] = oiraw['type'].str[0].str.lower()
    # py_vollib_vectorized.implied_volatility.vectorized_implied_volatility(price, S, K, t, r, flag, q=None, *, on_error='warn',
    #                                    model='black_scholes', return_as='dataframe', dtype=<class 'numpy.float64'>, **kwargs)
    return price_dataframe(oiraw, flag_col='Flag', underlying_price_col='underlyingValue', strike_col='strikePrice', annualized_tte_col='tte',
                     riskfree_rate_col='int', price_col='ltP', model='black_scholes', inplace=False)


def consolidated(nearmonth, expiryDates):
    items = [datetime.strptime(d, '%d-%b-%Y').date() for d in expiryDates]
    nearlist1 = []
    nearlist2 = []
    for r in range(4):
        a = list(filter(lambda d: (d.month == today.month + r), items))
        if len(a) > 0:
            if 0 < r < 3:
                nearlist1.append(max(a).strftime('%d-%b-%Y'))
            else:
                for i in a:
                    nearlist1.append(i.strftime('%d-%b-%Y'))
            if 1 < r:
                nearlist2.append(max(a).strftime('%d-%b-%Y'))
            else:
                for i in a:
                    nearlist2.append(i.strftime('%d-%b-%Y'))
    return nearlist1 if nearlist1 [0] != nearmonth else nearlist2


def fetchExpiry(datelist):
    print('categorising expiry dates')
    s = pd.Series(pd.to_datetime(datelist))
    monthly = s.groupby(s.dt.strftime('%Y-%m')).max().dt.strftime('%d-%b-%Y').tolist()
    weekly = list(set(datelist) - set(monthly))
    current = nearest(datelist)
    nearmonth = nearest(monthly)
    extracted = consolidated(nearmonth, datelist)
    return current, nearmonth, weekly, monthly, extracted


def update_expiry():
    print('need to update expiry dates from online data')
    expiryDates = option_chain(symbol)['records']['expiryDates']
    nearestwExpiry, nearmonthExpiry, wExpiry, mExpiry, consolidated = fetchExpiry(expiryDates)
    expiryDf = pd.DataFrame()
    eDf1 = pd.DataFrame()
    eDf2 = pd.DataFrame()
    eDf3 = pd.DataFrame()
    eDf1 = eDf1.assign(mExpiry=mExpiry)
    eDf2 = eDf2.assign(wExpiry=wExpiry)
    eDf3 = eDf3.assign(consolidated=consolidated)
    expiryDf = pd.concat([eDf1, eDf2, eDf3], axis=1)
    expiryDf.loc[0, 'nearestwExpiry'] = nearestwExpiry
    expiryDf.loc[0, 'nearmonthExpiry'] = nearmonthExpiry
    expiryDf.to_sql(name='expiry', con=wpdb, index=False, if_exists='replace',
                    dtype={'nearestwExpiry': sqlalchemy.types.VARCHAR(25),
                           'nearmonthExpiry': sqlalchemy.types.VARCHAR(25),
                           'consolidated': sqlalchemy.types.VARCHAR(25),
                           'wExpiry': sqlalchemy.types.VARCHAR(25),
                           'mExpiry': sqlalchemy.types.VARCHAR(25)
                           })
    return True


def expiry_db():
    print('getting expiry status')
    myQuery = '''SELECT * FROM {0};'''.format('expiry')
    expirydb = pd.read_sql_query(myQuery, wpdb, coerce_float=False)
    # print(expiryDf)
    if expirydb['nearestwExpiry'][0] < today.strftime('%d-%b-%Y'):
        print('need to update expiry db list to latest')
        updatedb_response = update_expiry()
        if updatedb_response:
            updated_expirydb = pd.read_sql_query(myQuery, wpdb, coerce_float=False)
            print('updated offline expiry db')
            return updated_expirydb
    else:
        print('fetched offline expiry db')
        return expirydb


def fno_status(symbol):
    openInterest = 0
    changeinOpenInterest = 0
    url = "https://www.nseindia.com/api/quote-derivative?symbol=" + symbol
    response = url_to_json(url)
    mexpiry = expiry_db()['nearmonthExpiry'] [0]
    for key in response['stocks']:
        if key['metadata']['instrumentType'] == 'Index Futures':
            openInterest += key['marketDeptOrderBook']['tradeInfo']['openInterest']
            changeinOpenInterest += key['marketDeptOrderBook']['tradeInfo']['changeinOpenInterest']
            if key['metadata']['expiryDate'] == mexpiry:
                value = key['metadata']
                fOpen = value['openPrice'];
                fPrevClose = value['prevClose'];
                fLtp = value['lastPrice']
    return fOpen, fPrevClose, fLtp, openInterest, changeinOpenInterest


#     return  {'Open': fOpen, 'PrevClose' : fPrevClose, 'ltp' : fLtp, 'OpenInterest' : openInterest, 'changeinOpenInterest': changeinOpenInterest}


def fetch_oi(symbol):
    geeks = ''
    table = symbol + '_oidata_live'
    tries = 1
    max_retries = 3
    while tries <= max_retries:
        try:
            print('calling option chain')
            raw_oi = option_chain(symbol)
            ce_values = [data["CE"] for data in raw_oi['records']['data'] if "CE" in data]
            pe_values = [data["PE"] for data in raw_oi['records']['data'] if "PE" in data]
            ce_data = pd.DataFrame(ce_values)
            pe_data = pd.DataFrame(pe_values)
            ce_data['type'] = "CE"
            pe_data['type'] = "PE"
            oidata = pd.concat([ce_data, pe_data])
            print("getting expiry date's")
            expirydb = expiry_db()
            wExpiry = expirydb['wExpiry']
            mExpiry = expirydb['mExpiry']
            oidata.loc[oidata['expiryDate'].isin(wExpiry), 'expiryType'] = 'w'
            oidata.loc[oidata['expiryDate'].isin(mExpiry), 'expiryType'] = 'm'
            oidata = oidata.drop(
                ['askPrice', 'askQty', 'bidQty', 'bidprice', 'totalTradedVolume', 'totalBuyQuantity', 'totalSellQuantity',
                 'underlying'], axis=1)
            oidata.columns = ['strikePrice', 'expiryDate', 'identifier', 'OI', 'OIChange', 'pOIChange', 'iV', 'ltP', 'change',
                              'pChange', 'underlyingValue', 'type', 'expiryType']
            oidata = oidata.sort_values(['expiryDate', 'strikePrice'], ascending=[True, False])
            oidata['TimeStamp'] = datetime.now().strftime("%Y-%m-%d, %H:%M")
            print('calculating option geeks')
            geeks = geeks_calc(oidata)
            # Reformat expiry date and strike price post geeks calculation
            oidata['expiryDate'] = oidata['expiryDate'].dt.strftime('%d-%b-%Y')
            oidata['strikePrice'] = oidata['strikePrice'].astype(int)
            oidata_table = pd.concat([oidata, geeks], axis=1)
            # oidata_table['type'] = oidata_table['Flag']
            oidata_table['IV'] = round(oidata_table['IV'], 4)
            oidata_table ['delta'] = round(oidata_table ['delta'], 6)
            oidata_table ['gamma'] = round(oidata_table ['gamma'], 6)
            oidata_table ['theta'] = round(oidata_table ['theta'], 6)
            oidata_table ['vega'] = round(oidata_table ['vega'], 6)
            oidata_table ['rho'] = round(oidata_table ['rho'], 6)
            print(oidata_table)
            if not oidata_table.empty:
                oidata_table['IV'] = oidata_table['IV'].replace(to_replace=0, method='bfill').values
                oidata_table.to_sql(name=table, con=wpdb, index=False, if_exists='append',
                              dtype={'TimeStamp': sqlalchemy.types.TIMESTAMP(timezone=False),
                                     'strikePrice': sqlalchemy.types.VARCHAR(25),
                                     'identifier': sqlalchemy.types.VARCHAR(50),
                                     'expiryDate': sqlalchemy.types.VARCHAR(25),
                                     'OI': sqlalchemy.types.Integer(),
                                     'OIChange': sqlalchemy.types.Float(),
                                     'iV': sqlalchemy.types.Integer(),
                                     'ltP': sqlalchemy.types.Float(),
                                     'delta': sqlalchemy.types.Float(),
                                     'gamma': sqlalchemy.types.Float(),
                                     'theta': sqlalchemy.types.Float(),
                                     'vega': sqlalchemy.types.Float(),
                                     'rho': sqlalchemy.types.Float(),
                                     'tte': sqlalchemy.types.Float(),
                                     'change': sqlalchemy.types.Integer(),
                                     'pChange': sqlalchemy.types.Float(),
                                     'underlyingValue': sqlalchemy.types.Float(),
                                     'type': sqlalchemy.types.VARCHAR(2),
                                     'expiryType': sqlalchemy.types.VARCHAR(2)
                                     })

        except Exception as error:
            print("error {0}".format(error))
            tries += 1
            sleep(10)
            continue

    if tries >= max_retries:
        print("max retries exceeded, no new data at {0}".format(datetime.now()))


def intraday_data(symbol):
    table = symbol + '_intraday_live'
    read_table = symbol + '_oidata_live'
    myQuery = '''SELECT * FROM {0};'''.format(read_table)
    oidata = pd.read_sql_query(myQuery, wpdb, coerce_float=False)
    for
        p_c_r = round(oidata['oI_pe'].sum() / oidata['oI_ce'].sum(), 2)
        p_c_c_r = round(oidata['change_ce'].sum() / oidata['change_pe'].sum(), 2)
        oi_change = round(oidata['changeinOI_ce'].sum() / oidata['changeinOI_pe'].sum(), 2)
        call_decay = round(oidata.nlargest(5, 'oI_ce', keep='last')['change_ce'].mean(), 2)
        put_decay = round(oidata.nlargest(5, 'oI_pe', keep='last')['change_pe'].mean(), 2)
        ltp = oidata['spotPrice'].values[0]
        strikes = oidata['strikePrice']
        expiry = oidata['expiryDate'].values[0]
        geeks = geeks_calc(ltp, strikes, expiry, vix)
        oidata = pd.merge(oidata, geeks)
        losses = [total_loss_at_strike(oidata, strike) / 100000 for strike in strikes]
        m = losses.index(min(losses))
        maxpain = strikes[m]

        oidata["calldata_ce"] = oidata['strikePrice'] * oidata['oI_ce']
        oidata["putdata_pe"] = oidata['strikePrice'] * oidata['oI_pe']
        oidata["oi"] = oidata["calldata_ce"] + oidata["putdata_pe"]
        # way of doing it to get only single value in int
        maxpain2 = oidata.loc[oidata['oi'] == oidata['oi'].max()]['strikePrice'].values[0]

        dt_today = date.today()
        recentdt = datetime(dt_today.year, dt_today.month, dt_today.day)
        expirydt = datetime.strptime(expiry, "%d-%b-%Y")
        days = (expirydt - recentdt).days + (12/24)
        adj = 0.8
        adj_vix = round(vix * adj, 2)
        adj_dvix = round(dvix * adj, 2)

        atm_ce_i, atm_pe_i, _, _ = get_nearest(strikes, ltp)
        atm_ce_ii, atm_pe_ii, atm_ce_iii, atm_pe_iii = get_nearest(strikes, dayopen)
        # atm_pe_ii = atm_ce_ii
        # atm_pe_iii = atm_ce_iii
        avg_iv = (oidata.loc[oidata['strikePrice'] == atm_ce_i]['iV_ce'].values[0] + oidata.loc[oidata['strikePrice'] == atm_pe_i]['iV_ce'].values[0]) / 2
        if time(9, 16) <= datetime.now().time() <= time(23, 25):
            # Store Daily maxpain to File at beganing of day.
            filewrite = open('DailyMaxpain.txt', 'w+')
            insert = ','.join(str(v) for v in [maxpain2, round((avg_iv/math.sqrt(248)), 2)])
            filewrite.write(insert)
            filewrite.close()

        maxpainfileread = open('DailyMaxpain.txt', 'r')
        dailymaxpain, live_avg_iv = [float(x) for x in maxpainfileread.read().strip().split(",")]
        maxpainfileread.close()
        dvx = live_avg_iv * math.sqrt(days)

        # Weekly Range based on 1 day before Expiry.
        if (expirydt - recentdt).days == 1:
            # Store MaxPain 1 day before Expiry to File.
            filewrite = open('ExpiryMaxPain.txt', 'w+')
            filewrite.write(str(maxpain2))
            filewrite.close()

        # Weekly Range based on Thursday close.
        if dt_today.weekday() == 4:
            # Store Thursday dayClose to File on Friday.
            filewrite = open('ThursdayClose.txt', 'w+')
            filewrite.write(str(prevclose))
            filewrite.close()

        if (expirydt - recentdt).days == 0:

            if abs(pchange) > ((dvx * days) * 0.5):
                d_upper_value = dayopen * (1 + (dvx / 100))
                d_lower_value = dayopen * (1 - ((dvx * 1.25) / 100))

                bull_upper_adj = dayopen * (1 + ((dvx * 1.5) / 100))
                bull_lower_adj = dayopen * (1 - ((dvx * 0.5) / 100))

                bear_upper_adj = dayopen * (1 + ((dvx * 0.5) / 100))
                bear_lower_adj = dayopen * (1 - ((dvx * 1.5) / 100))
            else:
                fileread = open('ExpiryMaxPain.txt', 'r')
                expiry_maxpain = float(fileread.read())
                fileread.close()

                d_upper_value = expiry_maxpain * (1 + (dvx / 100))
                d_lower_value = expiry_maxpain * (1 - (dvx / 100))

                bull_upper_adj = expiry_maxpain * (1 + ((dvx * 1.5) / 100))
                bull_lower_adj = expiry_maxpain * (1 - ((dvx * 0.5) / 100))

                bear_upper_adj = expiry_maxpain * (1 + ((dvx * 0.5) / 100))
                bear_lower_adj = expiry_maxpain * (1 - ((dvx * 1.5) / 100))

        elif dt_today.weekday() == 5:
            if not writemaxpain:
                # Store Friday maxpain to File on Friday.
                filewrite = open('FridayMaxpain.txt', 'w')
                filewrite.write(str(maxpain2))
                filewrite.close()
                writemaxpain = True

            d_upper_value = dayopen * (1 + (dvx / 100))
            d_lower_value = dayopen * (1 - (dvx / 100))

            bull_upper_adj = dayopen * (1 + ((dvx * 1.2) / 100))
            bull_lower_adj = dayopen * (1 - ((dvx * 0.8) / 100))

            bear_upper_adj = dayopen * (1 + ((dvx * 0.85) / 100))
            bear_lower_adj = dayopen * (1 - ((dvx * 1.25) / 100))

        else:
            d_upper_value = dayopen * (1 + (dvx / 100))
            d_lower_value = dayopen * (1 - (dvx / 100))

            bull_upper_adj = dayopen * (1 + ((dvx * 1.2) / 100))
            bull_lower_adj = dayopen * (1 - ((dvx * 0.8) / 100))

            bear_upper_adj = dayopen * (1 + ((dvx * 0.85) / 100))
            bear_lower_adj = dayopen * (1 - ((dvx * 1.25) / 100))

        fileread = open('ThursdayClose.txt', 'r')
        expiryclose = float(fileread.read())
        fileread.close()

        fileread = open('FridayMaxpain.txt', 'r')
        friday_maxpain = float(fileread.read())
        fileread.close()

        w_upper_maxpain = friday_maxpain * (1 + (wvix / 100))
        w_lower_maxpain = friday_maxpain * (1 - (wvix / 100))

        w_upper_value = expiryclose * (1 + (wvix / 100))
        w_lower_value = expiryclose * (1 - (wvix / 100))

        w_ce_i, _, _, _ = get_nearest(strikes, w_upper_value)
        _, w_pe_i, _, _ = get_nearest(strikes, w_lower_value)
        _, _, w_ce_ii, _ = get_nearest(strikes, w_upper_maxpain)
        _, _, _, w_pe_ii = get_nearest(strikes, w_lower_maxpain)

        d_ce_i, _, _, _ = get_nearest(strikes, d_upper_value)
        d_pe_i, _, _, _ = get_nearest(strikes, d_lower_value)

        _, bull_ce_adj, _, _ = get_nearest(strikes, bull_upper_adj)
        bull_pe_adj, _, _, _ = get_nearest(strikes, bull_lower_adj)

        bear_ce_adj, _, _, _ = get_nearest(strikes, bear_upper_adj)
        _, bear_pe_adj, _, _ = get_nearest(strikes, bear_lower_adj)

        scalper_ce = oidata.loc[oidata['strikePrice'] > atm_ce_i].sort_values(['iV_ce', 'gamma_ce'])
        scalper_ce = scalper_ce[scalper_ce != 0].dropna(subset=['iV_ce', 'gamma_ce'], inplace=False).Values[3]
        scalper_pe = oidata.loc[oidata['strikePrice'] < atm_pe_i].sort_values(['iV_pe', 'gamma_pe'])
        scalper_pe = scalper_pe[scalper_pe != 0].dropna(subset=['iV_pe', 'gamma_pe'], inplace=False).Values[3]

        mp_dict = {datetime.now().strftime("%H%M"): {
            'PreviousClose': prevclose,
            'Open': dayopen,
            'SpotPrice': ltp,
            'vix': vix,
            'adj vix': adj_vix,
            'mvix': mvix,
            'wvix': wvix,
            'dvix': dvix,
            'adj dvix': adj_dvix,
            'MaxPain': maxpain,
            'MaxPain-II': maxpain2,
            'put_decay': put_decay,
            'call_decay': call_decay,
            'Daily Range': int((live_avg_iv / 100) * dayopen * days) if (expirydt - recentdt).days == 0 else int((live_avg_iv / 100) * dayopen),
            'PCR': p_c_r,
            'PCCR': p_c_c_r,
            'OI_Chg_Ratio': oi_change,
            'Highest OI CE Strike': oidata.iloc[oidata['oI_ce'].argmax()]['strikePrice'],
            'Highest OI CE': oidata.iloc[oidata['oI_ce'].argmax()]['oI_ce'],
            'Highest OI Change CE Strike': oidata.iloc[oidata['changeinOI_ce'].argmax()]['strikePrice'],
            'Highest OI Change CE': oidata.iloc[oidata['changeinOI_ce'].argmax()]['changeinOI_ce'],
            'Highest OI PE Strike': oidata.iloc[oidata['oI_pe'].argmax()]['strikePrice'],
            'Highest OI PE': oidata.iloc[oidata['oI_pe'].argmax()]['oI_pe'],
            'Highest OI Change PE Strike': oidata.iloc[oidata['changeinOI_pe'].argmax()]['strikePrice'],
            'Highest OI Change PE': oidata.iloc[oidata['changeinOI_pe'].argmax()]['changeinOI_pe'],
            'Live-ATM CE': atm_ce_i,
            'Live-ATM CE-IV': oidata.loc[oidata['strikePrice'] == atm_ce_i]['iV_ce'].values[0],
            'Live-ATM CE-Delta': oidata.loc[oidata['strikePrice'] == atm_ce_i]['delta_ce'].values[0],
            'Live-ATM CE-ltp': oidata.loc[oidata['strikePrice'] == atm_ce_i]['ltP_ce'].values[0],
            'Live-ATM PE': atm_pe_i,
            'Live-ATM PE-IV': oidata.loc[oidata['strikePrice'] == atm_pe_i]['iV_pe'].values[0],
            'Live-ATM PE-Delta': oidata.loc[oidata['strikePrice'] == atm_pe_i]['delta_ce'].values[0],
            'Live-ATM PE-ltp': oidata.loc[oidata['strikePrice'] == atm_ce_i]['ltP_ce'].values[0],
            'Scalper CE': scalper_ce['strikePrice'].values[0],
            'Scalper CE-IV': scalper_ce['iV_ce'].values[0],
            'Scalper CE-Delta': scalper_ce['delta_ce'].values[0],
            'Scalper CE-Gamma': scalper_ce['gamma_ce'].values[0],
            'Scalper PE': scalper_pe['strikePrice'].values[0],
            'Scalper PE-IV': scalper_pe['iV_pe'].values[0],
            'Scalper PE-Delta': scalper_pe['delta_pe'].values[0],
            'Scalper PE-Gamma': scalper_pe['gamma_pe'].values[0],
            'Dly CE': d_ce_i,
            'Dly CE-IV': oidata.loc[oidata['strikePrice'] == d_ce_i]['iV_ce'].values[0],
            'Dly CE-Delta': oidata.loc[oidata['strikePrice'] == d_ce_i]['delta_ce'].values[0],
            'Dly CE-ltp': oidata.loc[oidata['strikePrice'] == d_ce_i]['ltP_ce'].values[0],
            'Dly PE': d_pe_i,
            'Dly PE-IV': oidata.loc[oidata['strikePrice'] == d_pe_i]['iV_pe'].values[0],
            'Dly PE-Delta': oidata.loc[oidata['strikePrice'] == d_pe_i]['delta_pe'].values[0],
            'Dly PE-ltp': oidata.loc[oidata['strikePrice'] == d_pe_i]['ltP_pe'].values[0],
            'Bull CE adj': bull_ce_adj,
            'Bull CE adj-IV': oidata.loc[oidata['strikePrice'] == bull_ce_adj]['iV_ce'].values[0],
            'Bull CE adj-Delta': oidata.loc[oidata['strikePrice'] == bull_ce_adj]['delta_ce'].values[0],
            'Bull CE adj-ltp': oidata.loc[oidata['strikePrice'] == bull_ce_adj]['ltP_ce'].values[0],
            'Bull PE adj': bull_pe_adj,
            'Bull PE adj-IV': oidata.loc[oidata['strikePrice'] == bull_pe_adj]['iV_pe'].values[0],
            'Bull PE adj-Delta': oidata.loc[oidata['strikePrice'] == bull_pe_adj]['delta_pe'].values[0],
            'Bull PE adj-ltp': oidata.loc[oidata['strikePrice'] == bull_pe_adj]['ltP_pe'].values[0],
            'Bear CE adj': bear_ce_adj,
            'Bear CE adj-IV': oidata.loc[oidata['strikePrice'] == bear_ce_adj]['iV_ce'].values[0],
            'Bear CE adj-Delta': oidata.loc[oidata['strikePrice'] == bear_ce_adj]['delta_ce'].values[0],
            'Bear CE adj-ltp': oidata.loc[oidata['strikePrice'] == bear_ce_adj]['ltP_ce'].values[0],
            'Bear PE adj': bear_pe_adj,
            'Bear PE adj-IV': oidata.loc[oidata['strikePrice'] == bear_pe_adj]['iV_pe'].values[0],
            'Bear PE adj-Delta': oidata.loc[oidata['strikePrice'] == bear_pe_adj]['delta_pe'].values[0],
            'Bear PE adj-ltp': oidata.loc[oidata['strikePrice'] == bear_pe_adj]['ltP_pe'].values[0],
            'Far ATM CE': atm_ce_iii,
            'Far ATM CE-IV': oidata.loc[oidata['strikePrice'] == atm_ce_iii]['iV_ce'].values[0],
            'Far ATM CE-Delta': oidata.loc[oidata['strikePrice'] == atm_ce_iii]['delta_ce'].values[0],
            'Far ATM CE-ltp': oidata.loc[oidata['strikePrice'] == atm_ce_iii]['ltP_ce'].values[0],
            'Far ATM PE': atm_pe_iii,
            'Far ATM PE-IV': oidata.loc[oidata['strikePrice'] == atm_pe_iii]['iV_pe'].values[0],
            'Far ATM PE-Delta': oidata.loc[oidata['strikePrice'] == atm_pe_iii]['delta_pe'].values[0],
            'Far ATM PE-ltp': oidata.loc[oidata['strikePrice'] == atm_pe_iii]['ltP_pe'].values[0],
            'ATM CE': atm_ce_ii,
            'ATM CE-IV': oidata.loc[oidata['strikePrice'] == atm_ce_ii]['iV_ce'].values[0],
            'ATM CE-Delta': oidata.loc[oidata['strikePrice'] == atm_ce_ii]['delta_ce'].values[0],
            'ATM CE-ltp': oidata.loc[oidata['strikePrice'] == atm_ce_ii]['ltP_ce'].values[0],
            'ATM PE': atm_pe_ii,
            'ATM PE-IV': oidata.loc[oidata['strikePrice'] == atm_pe_ii]['iV_pe'].values[0],
            'ATM PE-Delta': oidata.loc[oidata['strikePrice'] == atm_pe_ii]['delta_pe'].values[0],
            'ATM PE-ltp': oidata.loc[oidata['strikePrice'] == atm_pe_ii]['ltP_pe'].values[0],
            'MaxPain CE': dailymaxpain,
            'MaxPain CE-IV': oidata.loc[oidata['strikePrice'] == dailymaxpain]['iV_ce'].values[0],
            'MaxPain CE-Delta': oidata.loc[oidata['strikePrice'] == dailymaxpain]['delta_ce'].values[0],
            'MaxPain CE-ltp': oidata.loc[oidata['strikePrice'] == dailymaxpain]['ltP_ce'].values[0],
            'MaxPain PE': dailymaxpain,
            'MaxPain PE-IV': oidata.loc[oidata['strikePrice'] == dailymaxpain]['iV_pe'].values[0],
            'MaxPain PE-Delta': oidata.loc[oidata['strikePrice'] == dailymaxpain]['delta_pe'].values[0],
            'MaxPain PE-ltp': oidata.loc[oidata['strikePrice'] == dailymaxpain]['ltP_pe'].values[0],
            'Wly CE': w_ce_i,
            'Wly CE-IV': oidata.loc[oidata['strikePrice'] == w_ce_i]['iV_ce'].values[0],
            'Wly CE-Delta': oidata.loc[oidata['strikePrice'] == w_ce_i]['delta_ce'].values[0],
            'Wly CE-ltp': oidata.loc[oidata['strikePrice'] == w_ce_i]['ltP_ce'].values[0],
            'Wly PE': w_pe_i,
            'Wly PE-IV': oidata.loc[oidata['strikePrice'] == w_pe_i]['iV_ce'].values[0],
            'Wly PE-Delta': oidata.loc[oidata['strikePrice'] == w_pe_i]['delta_pe'].values[0],
            'Wly PE-ltp': oidata.loc[oidata['strikePrice'] == w_pe_i]['ltP_pe'].values[0],
            'Wly CE-Maxpain': w_ce_ii,
            'Wly CE-MP-IV': oidata.loc[oidata['strikePrice'] == w_ce_ii]['iV_ce'].values[0],
            'Wly CE-MP-Delta': oidata.loc[oidata['strikePrice'] == w_ce_ii]['delta_ce'].values[0],
            'Wly CE-MP-ltp': oidata.loc[oidata['strikePrice'] == w_ce_ii]['ltP_ce'].values[0],
            'Wly PE-Maxpain': w_pe_ii,
            'Wly PE-MP-IV': oidata.loc[oidata['strikePrice'] == w_pe_ii]['iV_ce'].values[0],
            'Wly PE-MP-Delta': oidata.loc[oidata['strikePrice'] == w_pe_ii]['delta_pe'].values[0],
            'Wly PE-MP-ltp': oidata.loc[oidata['strikePrice'] == w_pe_ii]['ltP_pe'].values[0]
        }}

        mp_df = pd.DataFrame(mp_dict).transpose()
        mp_df['Time'] = timestamp
        mp_df['Day'] = datetime.now().strftime("%a")
        mp_df['Live-ATM Avg-IV'] = (mp_df['Live-ATM CE-IV'] + mp_df['Live-ATM PE-IV']) / 2
        mp_df['Wly Future'] = mp_df['SpotPrice'] + mp_df['Live-ATM CE-ltp'] - mp_df['Live-ATM PE-ltp']
        mp_df['Dly sum ltp'] = mp_df['Dly CE-ltp'] + mp_df['Dly PE-ltp']
        mp_df['Far ATM sum ltp'] = mp_df['Far ATM CE-ltp'] + mp_df['Far ATM PE-ltp']
        mp_df['ATM sum ltp'] = mp_df['ATM CE-ltp'] + mp_df['ATM PE-ltp']
        mp_df['MaxPain sum ltp'] = mp_df['MaxPain CE-ltp'] + mp_df['MaxPain PE-ltp']
        mp_df
        mp_df_rw = pd.concat([mp_df_rw, mp_df])
        mp_df_rw = mp_df_rw.reset_index(drop=True)
        mp_df_rw['Date'] = datetime.now().strftime('%d-%B-%Y')

        # Adjustment logic :
        # Stop Loss
        mp_df_rw['Dly Stop'] = round(mp_df_rw['Dly sum ltp'][0] + mp_df_rw['Dly CE-ltp'][0], 2)
        # Identify Index of condition occurrence in order to apply adjustment accordingly
        # Logic 1: If Daily Call LTP goes below 50% of Daily PUT LTP # CE LTP (1) < PE LTP (2) and vice versa nut market is not trending

        # ce_shift_logic_1 = mp_df_rw['Dly CE-ltp'] < (mp_df_rw['Dly PE-ltp'] * 0.5) and mp_df_rw['PCR'] > 0.65
        # pe_shift_logic_1 = mp_df_rw['Dly PE-ltp'] < (mp_df_rw['Dly CE-ltp'] * 0.5) and mp_df_rw['PCR'] < 1.25
        #
        # ce_shift_logic_2 = mp_df_rw['Dly CE-ltp'] < (mp_df_rw['Dly PE-ltp'] * 0.5) and mp_df_rw['PCR'] < 0.7 and mp_df_rw['Dly PE-Delta'] <= (mp_df_rw['Dly CE-Delta'] * 1.3)
        # pe_shift_logic_2 = mp_df_rw['Dly PE-ltp'] < (mp_df_rw['Dly CE-ltp'] * 0.5) and mp_df_rw['PCR'] > 1.2 and mp_df_rw['Dly CE-Delta'] <= (mp_df_rw['Dly PE-Delta'] * 1.3)

        # # Ratio Spread
        # mp_df_rw['ce_lot_size'] = 2 if mp_df_rw['Dly CE-ltp'][0] < (mp_df_rw['Dly PE-ltp'][0] * 0.5) \
        #                    and mp_df_rw['PCR'][0] < 0.7 \
        #                    and mp_df_rw['Dly PE-Delta'][0] > (mp_df_rw['Dly CE-Delta'][0] * 1.3) \
        #                    else mp_df_rw['ce_lot_size'] = 1
        #
        # mp_df_rw['pe_lot_size'] = 2 if mp_df_rw['Dly PE-ltp'][0] < (mp_df_rw['Dly CE-ltp'][0] * 0.5) \
        #                    and mp_df_rw['PCR'][0] > 1.2 \
        #                    and mp_df_rw['Dly CE-Delta'][0] > (mp_df_rw['Dly PE-Delta'][0] * 1.3) \
        #                    else mp_df_rw['pe_lot_size'] = 1

        # Dly_Bear_adj_Logic_1_idx = mp_df_rw.index[ce_logic_1][0]
        # Dly_Bull_adj_Logic_1_idx = mp_df_rw.index[pe_logic_1][0]
        #
        # Dly_CE_Bull_Adj_time = mp_df_rw['Time'][Dly_Bear_adj_Logic_1_idx]
        # Dly_PE_Bear_Adj_time = mp_df_rw['Time'][Dly_Bear_adj_Logic_1_idx]
        #
        # Dly_CE_initial_Stop = round(mp_df_rw['Dly sum ltp'][0] + mp_df_rw['Dly CE-ltp'][0], 2)
        # Dly_CE_Trailing_Stop = mp_df_rw[mp_df_rw['Time'] == '12:00']['Dly sum ltp'] + \
        #                        mp_df_rw[mp_df_rw['Time'] == '12:00']['Dly CE-ltp']
        #
        # Dly_CE_Bull_Adj_Stop = mp_df_rw['Dly sum ltp'][Dly_Bull_adj_Logic_1_idx] + \
        #                        mp_df_rw['Dly CE-ltp'][Dly_Bull_adj_Logic_1_idx]
        #
        # Dly_CE_Bear_Adj_Stop = mp_df_rw['Dly sum ltp'][Dly_Bear_adj_Logic_1_idx] + \
        #                        mp_df_rw['Dly CE-ltp'][Dly_Bear_adj_Logic_1_idx]
        #
        # Dly_PE_initial_Stop = round(mp_df_rw['Dly sum ltp'][0] + mp_df_rw['Dly PE-ltp'][0], 2)
        # Dly_PE_Trailing_Stop = mp_df_rw[mp_df_rw['Time'] == '12:00']['Dly sum ltp'] + \
        #                         mp_df_rw[mp_df_rw['Time'] == '12:00']['Dly PE-ltp']
        #
        # Dly_PE_Bull_Adj_Stop = mp_df_rw['Dly sum ltp'][Dly_Bull_adj_Logic_1_idx] + \
        #                        mp_df_rw['Dly PE-ltp'][Dly_Bull_adj_Logic_1_idx]
        #
        # Dly_PE_Bear_Adj_Stop = mp_df_rw['Dly sum ltp'][Dly_Bear_adj_Logic_1_idx] + \
        #                        mp_df_rw['Dly PE-ltp'][Dly_Bear_adj_Logic_1_idx]
        #
        # if mp_df_rw['Time'] > '12:00':
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_Trailing_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_Trailing_Stop
        #     # Bull Adjustment
        # elif mp_df_rw['Time'] < '12:00' > Dly_CE_Bull_Adj_time:
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_Bull_Adj_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_Bull_Adj_Stop
        # elif mp_df_rw['Time'] > '12:00' < Dly_CE_Bull_Adj_time:
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_Bull_Adj_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_Bull_Adj_Stop
        #     # Bear Adjustment
        # elif mp_df_rw['Time'] < '12:00' > Dly_PE_Bear_Adj_time:
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_Bear_Adj_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_Bear_Adj_Stop
        # elif mp_df_rw['Time'] > '12:00' < Dly_PE_Bear_Adj_time:
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_Bear_Adj_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_Bear_Adj_Stop
        # else:
        #     mp_df_rw['Dly CE Stoploss'] = Dly_CE_initial_Stop
        #     mp_df_rw['Dly PE Stoploss'] = Dly_PE_initial_Stop

        mp_df_rw.to_json(mp_filename, orient='index', compression='infer')

        if not df_rw.empty:
            df_rw = df_rw[
                ['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'pChange_ce',
                 'change_ce', 'ltP_ce', 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce',
                 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe',
                 'change_pe', 'pChange_pe', 'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']]

        oidata = oidata[
            ['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'pChange_ce',
             'change_ce',
             'ltP_ce', 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe',
             'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe',
             'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']]

        oidata_db = pd.concat([df_rw, oidata])
        oidata_db = oidata_db.reset_index(drop=True)

            oidata_db.to_json(oi_filename, orient='index', compression='infer')



# def update_live_data(dailydata, timenow):
#     try:
#         if not dailydata.empty:
#             gd.set_with_dataframe(gsh_oi_live, dailydata[['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce',
#                                                           'delta_ce', 'estimate_ce', 'pChange_ce', 'change_ce', 'ltP_ce',
#                                                           'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce',
#                                                           'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe',
#                                                           'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe',
#                                                           'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']])
#         else:
#             print("No Daily Data Received")
#             sleep(30)
#
#     except Exception as e:
#         print(e)
#         sys.stdout.flush()
#         pass
#
#     finally:
#         print(datetime.now() - timenow, "live OI sheet written")
#         pass


# def update_daily_oi(mp_df, timenow):
#     try:
#         if not mp_df.empty:
#             gd.set_with_dataframe(gsh_daily_oi_data,
#                                   mp_df[['Date', 'Day', 'Time', 'PreviousClose', 'Open', 'SpotPrice', 'Wly Future',
#                                          'MaxPain', 'MaxPain-II', 'PCR', 'PCCR', 'OI_Chg_Ratio', 'vix', 'adj vix', 'dvix',
#                                          'adj dvix', 'Daily Range', 'call_decay', 'put_decay',
#                                          'Highest OI CE Strike', 'Highest OI CE', 'Highest OI Change CE Strike',
#                                          'Highest OI Change CE',
#                                          'Highest OI PE Strike', 'Highest OI PE', 'Highest OI Change PE Strike',
#                                          'Highest OI Change PE',
#                                          'Live-ATM CE', 'Live-ATM CE-IV', 'Live-ATM CE-Delta',
#                                          'Live-ATM PE', 'Live-ATM PE-IV', 'Live-ATM PE-Delta', 'Live-ATM Avg-IV',
#                                          'Scalper CE', 'Scalper CE-IV', 'Scalper CE-Delta', 'Scalper CE-Gamma',
#                                          'Scalper PE', 'Scalper PE-IV', 'Scalper PE-Delta', 'Scalper PE-Gamma',
#                                          'Dly CE', 'Dly CE-IV', 'Dly CE-Delta', 'Dly CE-ltp',
#                                          'Dly PE', 'Dly PE-IV', 'Dly PE-Delta', 'Dly PE-ltp', 'Dly sum ltp',
#                                          # 'Dly CE Stoploss', 'Dly PE Stoploss', 'pe_lot_size', 'ce_lot_size'
#                                          'Bull CE adj', 'Bull CE adj-IV', 'Bull CE adj-Delta', 'Bull CE adj-ltp',
#                                          'Bull PE adj', 'Bull PE adj-IV', 'Bull PE adj-Delta', 'Bull PE adj-ltp',
#                                          'Bear CE adj', 'Bear CE adj-IV', 'Bear CE adj-Delta', 'Bear CE adj-ltp',
#                                          'Bear PE adj', 'Bear PE adj-IV', 'Bear PE adj-Delta', 'Bear PE adj-ltp',
#                                          'Far ATM CE', 'Far ATM CE-IV', 'Far ATM CE-Delta', 'Far ATM CE-ltp', 'Far ATM PE',
#                                          'Far ATM PE-IV', 'Far ATM PE-Delta', 'Far ATM PE-ltp', 'Far ATM sum ltp',
#                                          'ATM CE', 'ATM CE-IV', 'ATM CE-Delta', 'ATM CE-ltp', 'ATM PE',
#                                          'ATM PE-IV', 'ATM PE-Delta', 'ATM PE-ltp', 'ATM sum ltp',
#                                          'MaxPain CE', 'MaxPain CE-IV', 'MaxPain CE-Delta', 'MaxPain CE-ltp', 'MaxPain PE',
#                                          'MaxPain PE-IV', 'MaxPain PE-Delta', 'MaxPain PE-ltp', 'MaxPain sum ltp']])
#         else:
#             print("No Daily OI Data Received")
#             sleep(30)
#
#     except Exception as e:
#         print(e)
#         sys.stdout.flush()
#         pass
#
#     finally:
#         print(datetime.now() - timenow, "Daily sheet written")


# def update_weekly_oi(mp_df, timenow):
#     try:
#         if not mp_df.empty:
#             gd.set_with_dataframe(gsh_weekly_oi_data,
#                                   mp_df[['Time', 'PreviousClose', 'Open', 'SpotPrice', 'MaxPain', 'PCR', 'vix',
#                                          'call_decay', 'put_decay', 'Live-ATM CE',
#                                          'Live-ATM CE-IV', 'Live-ATM PE', 'Live-ATM PE-IV',
#                                          'wvix', 'Wly CE', 'Wly CE-IV', 'Wly CE-Delta',
#                                          'Wly CE-ltp', 'Wly PE', 'Wly PE-IV', 'Wly PE-Delta',
#                                          'Wly PE-ltp', 'Wly CE-Maxpain', 'Wly CE-MP-IV',
#                                          'Wly CE-MP-Delta', 'Wly CE-MP-ltp', 'Wly PE-Maxpain',
#                                          'Wly PE-MP-IV', 'Wly PE-MP-Delta', 'Wly PE-MP-ltp',
#                                          # 'Mly PE - I', 'Mly CE - I', 'Yearly PE - I', 'Yearly CE - I', 'Dly PE - II', 'Dly CE - II', 'Mly PE - II',
#                                          # 'Mly CE - II', 'mvix',
#                                          'MaxPain-II', 'adj vix', 'adj dvix']])
#         else:
#             print("No Weekly OI Data Received")
#             sleep(30)
#
#     except Exception as e:
#         print(e)
#         sys.stdout.flush()
#         pass
#
#     finally:
#         print(datetime.now() - timenow, "Weekly sheet written")


# def dump_to_sheet(df, timenow):
#     try:
#         # Write daily dump to to google sheets
#         gd.set_with_dataframe(gsh_daily_dump, df)
#
#     except Exception as e:
#         print(e)
#         sys.stdout.flush()
#         pass
#
#     finally:
#         print(datetime.now() - timenow, "daily dump sheet written")


def main():
    dvix, wvix, mvix, vix = get_vix(symbol)
    dayopen, prevclose, pchange = get_symbol_open_data(symbol)

    timeframe = 1
    slots = list(np.arange(0.0, 60.0))
    while time(9, 16) > datetime.now().time() >= time(00, 00):
        timenow = datetime.now()
        if timenow.minute / timeframe in slots:
            nextscan = timenow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe)
            forwardscan = timenow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe + 1)
            waitsecs = int(((forwardscan if nextscan < datetime.now() else nextscan) - datetime.now()).seconds + 30)
            if waitsecs > 0:
                print("waiting {0} Seconds for Market open, Timestamp : {1} ".format(waitsecs, datetime.now()))
                sleep(waitsecs)
            else:
                sleep(0)

    while time(9, 16) <= datetime.now().time() <= time(23, 50):
        timenow = datetime.now()
        if timenow.minute / timeframe in slots:
            fetch_oi()
            dtnow = datetime.now()
            recentdtm = datetime(dtnow.year, dtnow.month, dtnow.day, dtnow.hour, dtnow.minute, dtnow.second)
            recenttime = dtnow.strftime('%H:%M')

            nextscan = dtnow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe)
            print("nextscan", nextscan, "RecentScan", recentdtm)
            print(nextscan < recentdtm)
            forwardscan = dtnow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe + 1)
            # waitsecs = int(((forwardscan if nextscan < recentdtm or dailydata.Time[0] < recenttime else nextscan) - recentdtm).seconds)
            waitsecs = int(((forwardscan if nextscan < recentdtm else nextscan) - recentdtm).seconds)
            if waitsecs > 0:
                print("waiting {0} Seconds next daily scan, Timestamp : {1} ".format(waitsecs, datetime.now()))
                sleep(waitsecs)
            else:
                sleep(0)
            print(datetime.now() - timenow, "execution completed")
        else:
            print("No Daily Dump Received")
            sleep(30)


if __name__ == '__main__':
    main()
