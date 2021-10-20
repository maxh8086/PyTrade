from xlrd import open_workbook
import pymysql
import sqlalchemy
import pandas as pd
import xlrd
import threading
from datetime import datetime
engine = sqlalchemy.create_engine('mysql+pymysql://root:root@127.0.0.1:3306/market_data')

def getOptionsData():

    wb = open_workbook('F:/demo2.xlsm')
    sheet = wb.sheets()[0]
    keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]

    dict_list = []
    for row_index in range(1, sheet.nrows):
        d = {keys[col_index]: sheet.cell(row_index, col_index).value 
             for col_index in range(sheet.ncols)}
        dict_list.append(d)
    today = datetime.today().date()
    date_values = xlrd.xldate_as_datetime(sheet.cell(2, 1).value , wb.datemode)

    timestamp = datetime.combine(today, date_values.time())

    df = pd.DataFrame.from_dict(dict_list)

    df['Time']= timestamp
    df['Exp. Date'] = pd.to_datetime(df['Exp. Date'], format='%Y%m%d')
    df_pe = df[df['Option Type'] == "PE"]
    df_ce = df[df['Option Type'] == "CE"]
    df_pe.to_sql(name='oc_pe', con=engine, index=False, if_exists='append')
    df_ce.to_sql(name='oc_ce', con=engine, index=False, if_exists='append')
    print('Entry Done for ',timestamp , datetime.now())



def startTimer():
    interval = 300  # seconds
    threading.Timer(interval, startTimer).start()
    getOptionsData()


if __name__ == '__main__':
    startTimer()

