import requests
import pandas as pd
import numpy as np
import math

import pymysql
import sqlalchemy
from sqlalchemy import Table, Column, Float, Integer, String, MetaData, ForeignKey
from io import StringIO
from bs4 import BeautifulSoup

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from time import sleep

# init all necessary variables
today = date.today()
symbol = 'BANKNIFTY'
indices = 'NIFTY BANK'
table = symbol.lower()
EOD_DB_UPDATED = 0
BOD_DB_UPDATED = 0

# connect mySQL DB using sqlalchemy
engine = sqlalchemy.create_engine('mysql+pymysql://pyadmin:pyU$er#123@127.0.0.1:3306/eod_data')

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


def get_online_db(indices=indices, sdt=def_start, edt=def_end):
    indicsurl = "https://www1.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType=" + indices + "&fromDate=" + sdt + "&toDate=" + edt
    while True:
        response = old_url_raw(indicsurl)
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
            except AttributeError:
                break
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
            #             cursor.execute(updatequery)
            #             output = pyconnector.commit()
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
    online = get_online_db(indices, std, edt)

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
    prices['Date'] = pd.to_datetime(prices['Date']).dt.strftime('%Y-%m-%d').astype(str)
    prices = prices.drop_duplicates(subset=['Date'])
    prices['NaturalLog'] = np.log(prices.Close / prices.Close.shift(-1)).shift(1).fillna(0).astype(float).round(6)
    prices['StdDev'] = prices['NaturalLog'].rolling(252).std().fillna(0).astype(float).round(6)
    prices['W_HV'] = round(prices['StdDev'] * math.sqrt(5) * 100, 2)
    prices['M_HV'] = round(prices['StdDev'] * math.sqrt(22) * 100, 2)
    prices['Y_HV'] = round(prices['StdDev'] * math.sqrt(252) * 100, 2)
    df_to_sql(prices, table, 'eod_data')


def drop_table(table=table):
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
        rowcount = cursor2.fetchall()[0][0]
    except pymysql.ProgrammingError as e:
        if (e.args[0] == 1146):
            print("Table dosen't exist, need to backfill")
            output = None
            # eod_backfill(indices,table)
    finally:
        # To close the connection
        cursor1.close()
        cursor2.close()
        pyconnector.close()

        if output is None:
            print('initiated complete backfill')
            eod_backfill(indices, table)
        elif output[0] < start_of_year:
            print('Dropped old table and initiated complete backfill')
            drop_table(table)
            eod_backfill(indices, table)
        elif output[0] <= (today - timedelta(days=30)) and output[0] >= start_of_year:
            print('initiated full year backfill')
            beganing_year = start_of_year.strftime('%d-%m-%Y')
            update_db(table, indices, beganing_year, def_end)
        elif 0 < today.weekday() < 5 and output[0] != today and rowcount > 252:
            print('initiated backfill for weekdays')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 5 and output[0] != (today - timedelta(days=1)) and rowcount > 252:
            print('initiated backfill over weekend')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 6 and output[0] != (today - timedelta(days=2)) and rowcount > 252:
            print('initiated backfill over weekend')
            update_db(table, indices, def_start, def_end)
        elif today.weekday() == 0 and output[0] != (today - timedelta(days=3)) and rowcount > 252:
            print('initiated for weekend')
            update_db(table, indices, def_start, def_end)
        else:
            return get_db(table, def_start, def_end)

    return get_db(table, def_start, def_end)


def get_bod_online():
    table = "bod_data"
    indicsOHLCurl = "https://www.nseindia.com/api/equity-stockIndices?index=" + indices
    json_data = url_to_json(indicsOHLCurl)
    # print(json_data)
    result = [i for i in json_data['data'] if indices in i['symbol']]
    bod_df = pd.DataFrame(json_data['data'], columns=['symbol', 'open', 'previousClose'])
    bod_df.insert(loc=0, column='Date', value=today)
    bod_df['pChange'] = percentage_change(bod_df['previousClose'], bod_df['open'])
    df_to_sql(bod_df, table, table)
    return 1


def request_bod():
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
        if (e.args[0] == 1146):
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
        elif output[0] != today and today.weekday() < 5:
            print('updating bod for today')
            get_bod_online()
            return get_db(table)
        elif output[0] == today or today.weekday() >= 5:
            return get_db(table)
