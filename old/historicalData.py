import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import os


result = pd.DataFrame()
stage = 0
response = []

headers = {
    "Host": "www1.nseindia.com",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www1.nseindia.com/products/content/equities/equities/eq_security.htm",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With",
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

response = requests.get('https://www1.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType=NIFTY%2050&fromDate=01-08-2020&toDate=24-03-2021', headers=headers)

if (response.status_code == requests.codes.ok) :

    page_content = BeautifulSoup(response.content, "html.parser")

    try :
        a = page_content.find(id="csvContentDiv").get_text();
        a = a.replace(':', ", \n")

        with open("data.csv", "w") as f :
            f.write(a)

        df = pd.read_csv("data.csv",header=0,index_col=False,usecols=['Date','Close'])
        df.set_index("Date", inplace=True)
        df = df[: :-1]
        result = pd.concat([result, df])


    except AttributeError :
        # if(total_stages <= 1):
        print("No data available from " + str(fromdate) + " to " + str(todate))

try :
    os.remove("data.csv")
except(OSError) :
    pass

print(result)