from nsepython import *
from historicVolatility import get_vix
import os
import pandas as pd
import xlwings as xw
from time import sleep
from datetime import datetime, time, timedelta
import json
import numpy as np


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)

wb = xw.Book(fullname="Option_chain_analysis.xlsx")  # this will create a new workbook
sheet_oi_single = wb.sheets("sheet1")
sheet_live = wb.sheets("sheet3")
oi_database = wb.sheets('Sheet2')
# sheet_oi_single.range('A:AF').api.Delete()

sheet_oi_single.range('A:AF').api.Delete()
sheet_live.range('A:AF').api.Delete()
oi_database.range('A:AF').api.Delete()

symbol = 'NIFTY'

oi_filename = os.path.join("Files", "oi_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))
mp_filename = os.path.join("Files", "mp_data_records_{0}.json".format(datetime.now().strftime("%d%m%y")))


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


def fetch_oi(df, mp_df):
    df_list = [ ]
    mp_list = [ ]

    # strike_prices =[]
    tries = 1
    max_retries = 3
    while tries <= max_retries:
        try:
            r = option_chain(symbol)
            # for expiry in r['records']['expiryDates'] :
            #     ce_values = [data["CE"] for data in r['records']['data'] if "CE" in data and str(data['expiryDate'].lower() == str(expiry).lower())]
            #     pe_values = [data["PE"] for data in r['records']['data'] if "PE" in data and str(data['expiryDate'].lower() == str(expiry).lower())]
            ce_values = [data["CE"] for data in r['filtered']['data'] if "CE" in data]
            pe_values = [data["PE"] for data in r['filtered']['data'] if "PE" in data]
            ce_data = pd.DataFrame(ce_values)
            pe_data = pd.DataFrame(pe_values)
            ce_data = ce_data.sort_values(['strikePrice'])
            pe_data = pe_data.sort_values(['strikePrice'])

            # Need to check impact of labeling data
            # ce_data['type'] = 'ce'
            # pe_data['type'] = 'pe'

            oidata = pe_data.merge(ce_data, how='inner', on='strikePrice', suffixes=("_pe", "_ce"))

            oidata.drop(
                ['askPrice_pe', 'askQty_pe', 'bidQty_pe', 'bidprice_pe', 'identifier_pe', 'totalBuyQuantity_pe',
                  'totalSellQuantity_pe', 'underlyingValue_pe', 'underlying_pe', 'askPrice_ce', 'askQty_ce',
                  'bidQty_ce',
                  'bidprice_ce', 'expiryDate_ce', 'expiryDate_pe', 'identifier_ce', 'totalBuyQuantity_ce',
                  'totalSellQuantity_ce', 'underlying_ce'], axis=1, inplace=True)

            oidata.rename(columns={'openInterest_pe': 'oI_pe', 'changeinOpenInterest_pe': 'changeinOI_pe',
                                   'pchangeinOpenInterest_pe': 'pchangeinOI_pe',
                                   'totalTradedVolume_pe': 'Volume_pe', 'impliedVolatility_pe': 'iV_pe',
                                   'lastPrice_pe': 'ltP_pe', 'openInterest_ce': 'oI_ce',
                                   'changeinOpenInterest_ce': 'changeinOI_ce',
                                   'pchangeinOpenInterest_ce': 'pchangeinOI_ce', 'totalTradedVolume_ce': 'Volume_ce',
                                   'impliedVolatility_ce': 'iV_ce', 'lastPrice_ce': 'ltP_ce', 'underlyingValue_ce': 'spotPrice'}, inplace=True)

            oidata['pchangeinOI_ce'] = round(oidata['pchangeinOI_ce'], 2)
            oidata['pchangeinOI_pe'] = round(oidata['pchangeinOI_pe'], 2)
            oidata['pChange_ce'] = round(oidata['pChange_ce'], 2)
            oidata['pChange_pe'] = round(oidata['pChange_pe'], 2)

            oidata = oidata.sort_values(['strikePrice'])
            # print(oidata)
            sheet_oi_single.range("A1").options(index=False, header=True).value = oidata[['pChange_ce', 'change_ce', 'ltP_ce',
            'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]
            p_c_r = round(oidata['oI_pe'].sum() / oidata['oI_ce'].sum(), 2)
            call_decay = round(oidata.nlargest(5, 'oI_ce', keep='last')['change_ce'].mean(), 2)
            put_decay = round(oidata.nlargest(5, 'oI_pe', keep='last')['change_pe'].mean(), 2)
            ltp = oidata['spotPrice'].values[0]
            strike_prices = oidata['strikePrice']

            atm_ce_i, atm_pe_i, atm_ce_ii, atm_pe_ii = get_nearest(strike_prices, ltp)

            oidata["calldata_ce"] = oidata['strikePrice'] * oidata['oI_ce']
            oidata["putdata_pe"] = oidata['strikePrice'] * oidata['oI_pe']
            oidata["oi"] = oidata["calldata_ce"] + oidata["putdata_pe"]
            maxpain = oidata.loc[oidata['oi'] == oidata["oi"].max()]['strikePrice'].values[0]  # way of doing it to get only single value in int
            yUppervalue = maxpain * (1+(vix/100))
            yLowervalue = maxpain * (1-(vix/100))
            mUppervalue = maxpain * (1+(mvix/100))
            mLowervalue = maxpain * (1-(mvix/100))
            wUppervalue = maxpain * (1+(wvix/100))
            wLowervalue = maxpain * (1-(wvix/100))
            dUppervalue = maxpain * (1+(dvix/100))
            dLowervalue = maxpain * (1-(dvix/100))
            mUpperStrike_i, _, mUpperStrike_ii, _ = get_nearest(strike_prices, mUppervalue)
            _, mLowerStrike_i, _, mLowerStrike_ii = get_nearest(strike_prices, mLowervalue)
            wUpperStrike_i, _, wUpperStrike_ii, _ = get_nearest(strike_prices, wUppervalue)
            _, wLowerStrike_i, _, wLowerStrike_ii = get_nearest(strike_prices, wLowervalue)
            dUpperStrike_i, _, dUpperStrike_ii, _ = get_nearest(strike_prices, dUppervalue)
            _, dLowerStrike_i, _, dLowerStrike_ii = get_nearest(strike_prices, dLowervalue)

            if len(df_list) > 0:
                oidata['Time'] = df_list[-1][0]['Time']

            # if len(df_list) > 0 and oidata.to_dict('records') == df_list[-1]:
            if len(df_list) > 0 and oidata.to_dict() == df_list[-1]:
                print("Duplicate data, Not recording")
                sleep(10)
                tries += 1
                continue

            oidata['Time'] = datetime.now().strftime("%H:%M")
            # print(oidata)
            mp_dict = {datetime.now().strftime("%H:%M"): {
                                                          'SpotPrice': ltp,
                                                          'vix': vix,
                                                          'mvix': mvix,
                                                          'wvix': wvix,
                                                          'dvix': dvix,
                                                          'MaxPain': maxpain,
                                                          'PCR': p_c_r,
                                                          'Call ATM-I': atm_ce_i,
                                                          'Call ATM-I IV': oidata.loc[oidata['strikePrice'] == atm_ce_i]['iV_ce'].values[0],
                                                          'PUT ATM-I': atm_pe_i,
                                                          'PUT ATM-I IV': oidata.loc[oidata['strikePrice'] == atm_pe_i]['iV_pe'].values[0],
                                                          'Call ATM-II': atm_ce_ii,
                                                          'Call ATM-II IV': oidata.loc[oidata['strikePrice'] == atm_ce_ii]['iV_ce'].values[0],
                                                          'PUT ATM-II': atm_pe_ii,
                                                          'PUT ATM-II IV': oidata.loc[oidata['strikePrice'] == atm_pe_ii]['iV_pe'].values[0],
                                                          'Yearly Upper Strike - I': round(yUppervalue / 100) * 100,
                                                          'Yearly Lower Strike - I': round(yLowervalue / 100) * 100,
                                                          'Monthly Upper Strike - I': mUpperStrike_i,
                                                          'Monthly Lower Strike - I': mLowerStrike_i,
                                                          'Weekly Upper Strike - I': wUpperStrike_i,
                                                          'Weekly Lower Strike - I': wLowerStrike_i,
                                                          'Daily Upper Strike - I': dUpperStrike_i,
                                                          'Daily Lower Strike - I': dLowerStrike_i,
                                                          'Monthly Upper Strike - II': mUpperStrike_ii,
                                                          'Monthly Lower Strike - II': mLowerStrike_ii,
                                                          'Weekly Upper Strike - II': wUpperStrike_ii,
                                                          'Weekly Lower Strike - II': wLowerStrike_ii,
                                                          'Daily Upper Strike - II': dUpperStrike_ii,
                                                          'Daily Lower Strike - II': dLowerStrike_ii,
                                                          'put_decay': put_decay,
                                                          'call_decay': call_decay
                                                          }}

            df3 = pd.DataFrame(mp_dict).transpose()
            mp_df = pd.concat([mp_df, df3])
            oi_database.range("A1").options(header=True).value = mp_df
            with open(mp_filename, "w") as files:
                files.write(json.dumps(mp_df.to_dict(), indent=4, sort_keys=True))

            if not df.empty:
                df = df[['Time','pChange_ce', 'change_ce', 'ltP_ce',
            'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]

            oidata = oidata[['Time','pChange_ce', 'change_ce', 'ltP_ce',
            'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]

            df = pd.concat([df, oidata])

            df_list.append(oidata.to_dict())
            with open(oi_filename, "w") as files:
                files.write(json.dumps(df_list, indent=4, sort_keys=True))
            return df, mp_df
        except Exception as error:
            print("error {0}".format(error))
            tries += 1
            sleep(10)
            continue

    if tries >= max_retries:
        print("max retries exceeded, no new data at {0}".format(datetime.now()))
        return df, mp_df


def main():
    global df_list, dvix, wvix, mvix, vix

    dvix, wvix, mvix, vix = get_vix(symbol)

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
        mplist = json.loads(open(mp_filename).read())
        mp_df = pd.DataFrame().from_dict(mplist)
    except Exception as error:
        print("Error reading maxpain data from json file, Error {0}".format(error))
        # mp_list = []
        mp_df = pd.DataFrame()

    # Time loop starts from here
    timeframe = 5
    while time(9, 10) <= datetime.now().time() <= time(15, 30):
        timenow = datetime.now()
        check = True if timenow.minute/timeframe in list(np.arange(0.0, 12.0)) else False
        if check:
            nextscan = timenow + timedelta(minutes=timeframe)
            df, mp_df = fetch_oi(df, mp_df)
            # if not df.empty:
            #     df['iV'] = df['iV'].replace(to_replace=0, method='bfill').values
            #     df['identifier'] = df['strikePrice'].astype(str) + df['type']
            #     sheet_live.range("A1").value = df
            #     wb.api.RefreshAll()
            if not df.empty:
                df['iV_pe'] = df['iV_pe'].replace(to_replace=0, method='bfill').values
                df['iV_ce'] = df['iV_ce'].replace(to_replace=0, method='bfill').values
                # df['identifier'] = df['strikePrice'].astype(str) + df['type']
                sheet_live.range("A1").value = df
                wb.api.RefreshAll()
                waitsecs = int((nextscan - datetime.now()).seconds)
                print("wait for {0} Seconds for next scan".format(waitsecs))
                sleep(waitsecs) if waitsecs > 0 else sleep(0)
            else:
                print("No Data Received")
                sleep(30)

    # # ### code without time loop starts below ###
    # df, mp_df = fetch_oi(df, mp_df)
    # if not df.empty:
    #     df['iV_pe'] = df['iV_pe'].replace(to_replace=0, method='bfill').values
    #     df['iV_ce'] = df['iV_ce'].replace(to_replace=0, method='bfill').values
    #     # df['identifier'] = df['strikePrice'].astype(str) + df['type']
    #     sheet_live.range("A1").value = df
    #     wb.api.RefreshAll()
    # else:
    #     print("No Data Received")
    #     sleep(30)


if __name__ == '__main__':
    main()
