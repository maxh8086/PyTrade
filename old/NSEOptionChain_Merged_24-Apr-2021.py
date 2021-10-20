# Importing Third Party Library for NSE
from nsepython import *
import mibian

# Import In house Library for NSE
from historicVolatility import get_vix

# Import Python Library
import os
import pandas as pd
import xlwings as xw
from time import sleep
from datetime import datetime, time, timedelta, date
import json
import numpy as np
import math


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)

wb = xw.Book(fullname="Option_chain_analysis.xlsx")  # this will create a new workbook
sheet_oi_single = wb.sheets("sheet1")
sheet_live = wb.sheets("sheet3")
oi_database = wb.sheets('Sheet2')

sheet_oi_single.range('A:AZ').api.Delete()
sheet_live.range('A:AZ').api.Delete()
oi_database.range('A:AZ').api.Delete()

symbol = 'BANKNIFTY'

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


def geeks_calc(ltp, strikes, expiry, volatility):
    geeks_list = []
    int_rate = 10
    exp_str = datetime.strptime(expiry, '%d-%b-%Y')
    dt_expiry = date(int(exp_str.strftime('%Y')), int(exp_str.strftime('%m')), int(exp_str.strftime('%d')))
    dt_today = date.today()
    if dt_expiry > dt_today:
        daystoexpiry = (dt_expiry - dt_today).days
    else:
        daystoexpiry = 0.000001

    for strike in strikes:
        # BS([underlyingPrice, strikePrice, int_rate, daystoexpiry], volatility=x, callPrice=y, putPrice=z)
        c = mibian.BS([ltp, strike, int_rate, daystoexpiry], volatility=volatility)
        geeks_list.append([round(c.gamma, 4), round(c.vega, 4), round(c.callTheta, 2), round(c.callDelta, 2),
                           round(c.callPrice, 2), strike, round(c.putPrice, 2), round(c.putDelta, 2),
                           round(c.putTheta, 2), round(c.vega, 4),
                           round(c.gamma, 4)])
    # print(geeks_list)
    df_geeks = pd.DataFrame(geeks_list,
                            columns=['gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'strikePrice',
                                     'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe'])
    return df_geeks


def fetch_oi(df, mp_df):
    df_list = []
    # mp_list = []
    # strikes =[]

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

            oidata = pe_data.merge(ce_data, how='inner', on='strikePrice', suffixes=("_pe", "_ce"))

            oidata.drop(
                ['askPrice_pe', 'askQty_pe', 'bidQty_pe', 'bidprice_pe', 'identifier_pe', 'totalBuyQuantity_pe',
                 'totalSellQuantity_pe', 'underlyingValue_pe', 'underlying_pe', 'askPrice_ce', 'askQty_ce',
                 'bidQty_ce',
                 'bidprice_ce', 'expiryDate_pe', 'identifier_ce', 'totalBuyQuantity_ce',
                 'totalSellQuantity_ce', 'underlying_ce'], axis=1, inplace=True)

            oidata.rename(columns={'openInterest_pe': 'oI_pe', 'changeinOpenInterest_pe': 'changeinOI_pe',
                                   'pchangeinOpenInterest_pe': 'pchangeinOI_pe',
                                   'totalTradedVolume_pe': 'Volume_pe', 'impliedVolatility_pe': 'iV_pe',
                                   'lastPrice_pe': 'ltP_pe', 'openInterest_ce': 'oI_ce',
                                   'changeinOpenInterest_ce': 'changeinOI_ce',
                                   'pchangeinOpenInterest_ce': 'pchangeinOI_ce', 'totalTradedVolume_ce': 'Volume_ce',
                                   'impliedVolatility_ce': 'iV_ce', 'lastPrice_ce': 'ltP_ce',
                                   'underlyingValue_ce': 'spotPrice', 'expiryDate_ce': 'expiryDate'}, inplace=True)

            oidata['pchangeinOI_ce'] = round(oidata['pchangeinOI_ce'], 2)
            oidata['pchangeinOI_pe'] = round(oidata['pchangeinOI_pe'], 2)
            oidata['pChange_ce'] = round(oidata['pChange_ce'], 2)
            oidata['pChange_pe'] = round(oidata['pChange_pe'], 2)

            oidata = oidata.sort_values(['strikePrice'])
            timestamp = datetime.now().strftime("%H:%M")
            oidata['Time'] = timestamp

            p_c_r = round(oidata['oI_pe'].sum() / oidata['oI_ce'].sum(), 2)
            call_decay = round(oidata.nlargest(5, 'oI_ce', keep='last')['change_ce'].mean(), 2)
            put_decay = round(oidata.nlargest(5, 'oI_pe', keep='last')['change_pe'].mean(), 2)
            ltp = oidata['spotPrice'].values[0]
            strikes = oidata['strikePrice']
            expiry = oidata['expiryDate'].values[0]

            # print(geeks_calc(ltp, strikes, expiry, vix))
            geeks = geeks_calc(ltp, strikes, expiry, vix)
            oidata = pd.merge(oidata, geeks)
            # print(oidata)

            atm_ce_i, atm_pe_i, atm_ce_ii, atm_pe_ii = get_nearest(strikes, ltp)

            losses = [total_loss_at_strike(oidata, strike) / 100000 for strike in strikes]
            m = losses.index(min(losses))
            maxpain = strikes[m]

            oidata["calldata_ce"] = oidata['strikePrice'] * oidata['oI_ce']
            oidata["putdata_pe"] = oidata['strikePrice'] * oidata['oI_pe']
            oidata["oi"] = oidata["calldata_ce"] + oidata["putdata_pe"]
            # way of doing it to get only single value in int
            maxpain2 = oidata.loc[oidata['oi'] == oidata['oi'].max()]['strikePrice'].values[0]

            y_upper_value = maxpain * (1 + (vix / 100))
            y_lower_value = maxpain * (1 - (vix / 100))
            m_upper_value = maxpain * (1 + (mvix / 100))
            m_lower_value = maxpain * (1 - (mvix / 100))
            w_upper_value = maxpain * (1 + (wvix / 100))
            w_lower_value = maxpain * (1 - (wvix / 100))
            dt_today = date.today()
            if dt_today.weekday() == 3:
                # Shrunken Range for Expiry day
                dvx = dvix * math.sqrt(0.5)
            elif dt_today.weekday() == 4:
                # Higher range, Higher safety for volatile Friday
                dvx = dvix * math.sqrt(2)
            else:
                dvx = dvix
            d_upper_value = LastClose * (1 + (dvx / 100))
            d_lower_value = LastClose * (1 - (dvx / 100))
            m_ce_i, _, m_ce_ii, _ = get_nearest(strikes, m_upper_value)
            _, m_pe_i, _, m_pe_ii = get_nearest(strikes, m_lower_value)
            w_ce_i, _, w_ce_ii, _ = get_nearest(strikes, w_upper_value)
            _, w_pe_i, _, w_pe_ii = get_nearest(strikes, w_lower_value)
            d_ce_i, _, d_ce_ii, _ = get_nearest(strikes, d_upper_value)
            _, d_pe_i, _, d_pe_ii = get_nearest(strikes, d_lower_value)

            sheet_oi_single.range("A1").options(index=False, header=True).value = oidata[
                ['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'pChange_ce',
                 'change_ce',
                 'ltP_ce', 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe',
                 'oI_pe',
                 'changeinOI_pe', 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe', 'estimate_pe',
                 'delta_pe',
                 'theta_pe', 'vega_pe', 'gamma_pe']]

            # sheet_oi_single.range("A1").options(index=False, header=True).value = oidata[['pChange_ce', 'change_ce', 'ltP_ce',
            # 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            # 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]

            if len(df_list) > 0:
                oidata['Time'] = df_list[-1][0]['Time']

            # if len(df_list) > 0 and oidata.to_dict('records') == df_list[-1]:
            if len(df_list) > 0 and oidata.to_dict() == df_list[-1]:
                print("Duplicate data, Not recording")
                sleep(10)
                tries += 1
                continue

            mp_dict = {datetime.now().strftime("%H:%M"): {
                'SpotPrice': ltp,
                'vix': vix,
                'mvix': mvix,
                'wvix': wvix,
                'dvix': dvix,
                'MaxPain': maxpain,
                'MaxPain-II': maxpain2,
                'PCR': p_c_r,
                'ATM CE-I': atm_ce_i,
                'ATM CE-I IV': oidata.loc[oidata['strikePrice'] == atm_ce_i]['iV_ce'].values[0],
                'ATM PE-I': atm_pe_i,
                'ATM PE-I IV': oidata.loc[oidata['strikePrice'] == atm_pe_i]['iV_pe'].values[0],
                # 'ATM CE-II': atm_ce_ii,
                # 'ATM CE-II IV': oidata.loc[oidata['strikePrice'] == atm_ce_ii]['iV_ce'].values[0],
                # 'ATM PE-II': atm_pe_ii,
                # 'ATM PE-II IV': oidata.loc[oidata['strikePrice'] == atm_pe_ii]['iV_pe'].values[0],
                # 'Yly CE - I': round(y_upper_value / 100) * 100,
                # 'Yly PE - I': round(y_lower_value / 100) * 100,
                # 'Mly CE - I': m_ce_i,
                # 'Mly PE - I': m_pe_i,
                'Wly CE - I': w_ce_i,
                # 'Wly CE - I IV': oidata.loc[oidata['strikePrice'] == w_ce_i]['iV_ce'].values[0],
                'Wly PE - I': w_pe_i,
                # 'Wly CE - I IV': oidata.loc[oidata['strikePrice'] == w_pe_i]['iV_ce'].values[0],
                'Dly CE - I': d_ce_i,
                'Dly CE - I IV': oidata.loc[oidata['strikePrice'] == d_ce_i]['iV_ce'].values[0],
                'Dly PE - I': d_pe_i,
                'Dly PE - I IV': oidata.loc[oidata['strikePrice'] == d_pe_i]['iV_pe'].values[0],
                # 'Mly CE - II': m_ce_ii,
                # 'Mly PE - II': m_pe_ii,
                # 'Wly CE - II': w_ce_ii,
                # 'Wly PE - II': w_pe_ii,
                # 'Dly CE - II': d_ce_ii,
                # 'Dly PE - II': d_pe_ii,
                'put_decay': put_decay,
                'call_decay': call_decay
            }}

            df3 = pd.DataFrame(mp_dict).transpose()
            mp_df = pd.concat([mp_df, df3])

            oi_database.range("A1").options(header=True).value = mp_df[['SpotPrice', 'MaxPain', 'PCR',
                                                                        'call_decay', 'put_decay',
                                                                        'dvix',
                                                                        'Dly CE - I',
                                                                        'Dly CE - I IV',
                                                                        'Dly PE - I',
                                                                        'Dly PE - I IV',
                                                                        'vix',
                                                                        'ATM CE-I',
                                                                        'ATM CE-I IV',
                                                                        'ATM PE-I',
                                                                        'ATM PE-I IV',
                                                                        'wvix',
                                                                        'Wly PE - I',
                                                                        'Wly CE - I',
                                                                        # 'Mly PE - I',
                                                                        # 'Mly CE - I',
                                                                        # 'Yearly PE - I',
                                                                        # 'Yearly CE - I',
                                                                        # 'ATM CE-II',
                                                                        # 'ATM CE-II IV',
                                                                        # 'ATM PE-II',
                                                                        # 'ATM PE-II IV',
                                                                        # 'Dly PE - II',
                                                                        # 'Dly CE - II',
                                                                        # 'Wly PE - II',
                                                                        # 'Wly CE - II',
                                                                        # 'Mly PE - II',
                                                                        # 'Mly CE - II',
                                                                        # 'mvix',
                                                                        'MaxPain-II'
                                                                        ]]

            with open(mp_filename, "w") as files:
                files.write(json.dumps(mp_df.to_dict(), indent=4, sort_keys=True))

            # if not df.empty:
            #     df = df[['Time','pChange_ce', 'change_ce', 'ltP_ce',
            # 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            # 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]

            if not df.empty:
                df = df[
                    ['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'pChange_ce',
                     'change_ce',
                     'ltP_ce', 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe',
                     'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe',
                     'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']]

            oidata = oidata[
                ['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'pChange_ce',
                 'change_ce',
                 'ltP_ce', 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe',
                 'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe',
                 'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']]

            # oidata = oidata[['Time','pChange_ce', 'change_ce', 'ltP_ce',
            # 'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce', 'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe',
            # 'pchangeinOI_pe', 'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe']]

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
    global dvix, wvix, mvix, vix, LastClose

    dvix, wvix, mvix, vix, LastClose = get_vix(symbol)

    try:
        d_list = json.loads(open(oi_filename).read())
    except Exception as error:
        print("Error reading oi data from json file, Error {0}".format(error))
        d_list = []

    if d_list:
        df = pd.DataFrame()
        for item in d_list:
            df = pd.concat([df, pd.DataFrame(item)])
    else:
        df = pd.DataFrame()

    try:
        mplist = json.loads(open(mp_filename).read())
        mp_df = pd.DataFrame().from_dict(mplist)
    except Exception as error:
        print("Error reading maxpain data from json file, Error {0}".format(error))
        mp_df = pd.DataFrame()

    # Time loop starts from here
    # timeframe = 5
    timeframe = 1
    while time(9, 10) <= datetime.now().time() <= time(20, 30):
        timenow = datetime.now()
        check = True if timenow.minute / timeframe in list(np.arange(0.0, 60.0)) else False
        if check:
            nextscan = timenow + timedelta(minutes=timeframe)
            df, mp_df = fetch_oi(df, mp_df)
            if not df.empty:
                df['iV_pe'] = df['iV_pe'].replace(to_replace=0, method='bfill').values
                df['iV_ce'] = df['iV_ce'].replace(to_replace=0, method='bfill').values
                sheet_live.range("A1").value = df
                wb.api.RefreshAll()
                waitsecs = int((nextscan - datetime.now()).seconds)
                print("wait for {0} Seconds for next scan".format(waitsecs))
                sleep(waitsecs) if waitsecs > 0 else sleep(0)
            else:
                print("No Data Received")
                sleep(30)


if __name__ == '__main__':
    main()
