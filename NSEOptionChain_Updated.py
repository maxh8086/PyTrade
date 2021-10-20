# Importing Third Party Library for NSE
from nsepython import option_chain
import mibian

# Import In house Library for NSE
from historicVolatility import get_vix, get_symbol_open_data

# Import Python Library
import os
import sys
import pandas as pd
from time import sleep
from datetime import datetime, time, timedelta, date
import numpy as np
import math

import gspread
import gspread_dataframe as gd

# import logging
# import logging
# logging.basicConfig(level='WARNING')
# logging.basicConfig(level=logging.WARNING)


# initializing variable
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 1500)

gc = gspread.service_account()
gwb = gc.open("BNFOptionsDashboard")
gsh_daily_oi_data = gwb.worksheet("Daily OI Data")
gsh_weekly_oi_data = gwb.worksheet("Weekly OI Data")
gsh_oi_live = gwb.worksheet("OI Live")
gsh_daily_dump = gwb.worksheet("OI Dump")

gsh_daily_oi_data.clear()
gsh_weekly_oi_data.clear()
gsh_oi_live.clear()
gsh_daily_dump.clear()

gsh_daily_oi_data.format('1', {'textFormat': {'bold': True}})
gsh_weekly_oi_data.format('1', {'textFormat': {'bold': True}})
gsh_oi_live.format('1', {'textFormat': {'bold': True}})
gsh_daily_dump.format('1', {'textFormat': {'bold': True}})

symbol = 'BANKNIFTY'

if symbol == 'BANKNIFTY':
    indics = 'NIFTY BANK'
elif symbol == 'NIFTY':
    indics = 'NIFTY 50'
else:
    indics = symbol

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
    fmt = '%H:%M:%S'
    s1 = datetime.now().strftime(fmt)
    s2 = '15:30:00'  # Expiry End
    tdelta = datetime.strptime(s2, fmt) - datetime.strptime(s1, fmt)
    timetoexpire = (dt_expiry - dt_today).days + (tdelta.seconds / 86400)
    for strike in strikes:
        # BS([underlyingPrice, strikePrice, int_rate, timetoexpire], volatility=x, callPrice=y, putPrice=z)
        c = mibian.BS([ltp, strike, int_rate, timetoexpire], volatility=volatility)
        geeks_list.append([round(c.gamma, 4), round(c.vega, 4), round(c.callTheta, 4), round(c.callDelta, 4),
                           round(c.callPrice, 2), strike, round(c.putPrice, 2), round(c.putDelta, 4),
                           round(c.putTheta, 4), round(c.vega, 4),
                           round(c.gamma, 4)])
    df_geeks = pd.DataFrame(geeks_list,
                            columns=['gamma_ce', 'vega_ce', 'theta_ce', 'delta_ce', 'estimate_ce', 'strikePrice',
                                     'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe'])
    return df_geeks


def fetch_oi(df_rw, mp_df_rw, dvix, wvix, mvix, vix, dayopen, prevclose, pchange):
    oidata = ''
    # initializing variable
    writemaxpain = False
    # mp_list = []
    # strikes =[]

    tries = 1
    max_retries = 3
    while tries <= max_retries:
        try:
            r = option_chain(symbol)
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

                    # print("########################################################################################################################################")
                    # print("####################### Expiry Day: ", bull_upper_adj, "Bull Upper adj - 1", bull_lower_adj, "Bull Upper adj - 1 #######################")
                    # print("########################################################################################################################################")

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

                    # print("########################################################################################################################################")
                    # print("####################### Expiry Day: ", bull_upper_adj, "Bull Upper adj - 2", bull_lower_adj, "Bull Upper adj - 2 #######################")
                    # print("########################################################################################################################################")

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

            df_rw = pd.concat([df_rw, oidata])
            df_rw = df_rw.reset_index(drop=True)
            df_rw.to_json(oi_filename, orient='index', compression='infer')
            return df_rw, mp_df_rw, oidata
        except Exception as error:
            print("error {0}".format(error))
            tries += 1
            sleep(10)
            continue

    if tries >= max_retries:
        print("max retries exceeded, no new data at {0}".format(datetime.now()))
        return df_rw, mp_df_rw, oidata


def update_live_data(dailydata, timenow):
    try:
        if not dailydata.empty:
            gd.set_with_dataframe(gsh_oi_live, dailydata[['expiryDate', 'Time', 'gamma_ce', 'vega_ce', 'theta_ce',
                                                          'delta_ce', 'estimate_ce', 'pChange_ce', 'change_ce', 'ltP_ce',
                                                          'Volume_ce', 'pchangeinOI_ce', 'changeinOI_ce', 'oI_ce', 'iV_ce',
                                                          'strikePrice', 'iV_pe', 'oI_pe', 'changeinOI_pe', 'pchangeinOI_pe',
                                                          'Volume_pe', 'ltP_pe', 'change_pe', 'pChange_pe',
                                                          'estimate_pe', 'delta_pe', 'theta_pe', 'vega_pe', 'gamma_pe']])
        else:
            print("No Daily Data Received")
            sleep(30)

    except Exception as e:
        print(e)
        sys.stdout.flush()
        pass

    finally:
        print(datetime.now() - timenow, "live OI sheet written")
        pass


def update_daily_oi(mp_df, timenow):
    try:
        if not mp_df.empty:
            gd.set_with_dataframe(gsh_daily_oi_data,
                                  mp_df[['Date', 'Day', 'Time', 'PreviousClose', 'Open', 'SpotPrice', 'Wly Future',
                                         'MaxPain', 'MaxPain-II', 'PCR', 'PCCR', 'OI_Chg_Ratio', 'vix', 'adj vix', 'dvix',
                                         'adj dvix', 'Daily Range', 'call_decay', 'put_decay',
                                         'Highest OI CE Strike', 'Highest OI CE', 'Highest OI Change CE Strike',
                                         'Highest OI Change CE',
                                         'Highest OI PE Strike', 'Highest OI PE', 'Highest OI Change PE Strike',
                                         'Highest OI Change PE',
                                         'Live-ATM CE', 'Live-ATM CE-IV', 'Live-ATM CE-Delta',
                                         'Live-ATM PE', 'Live-ATM PE-IV', 'Live-ATM PE-Delta', 'Live-ATM Avg-IV',
                                         'Scalper CE', 'Scalper CE-IV', 'Scalper CE-Delta', 'Scalper CE-Gamma',
                                         'Scalper PE', 'Scalper PE-IV', 'Scalper PE-Delta', 'Scalper PE-Gamma',
                                         'Dly CE', 'Dly CE-IV', 'Dly CE-Delta', 'Dly CE-ltp',
                                         'Dly PE', 'Dly PE-IV', 'Dly PE-Delta', 'Dly PE-ltp', 'Dly sum ltp',
                                         # 'Dly CE Stoploss', 'Dly PE Stoploss', 'pe_lot_size', 'ce_lot_size'
                                         'Bull CE adj', 'Bull CE adj-IV', 'Bull CE adj-Delta', 'Bull CE adj-ltp',
                                         'Bull PE adj', 'Bull PE adj-IV', 'Bull PE adj-Delta', 'Bull PE adj-ltp',
                                         'Bear CE adj', 'Bear CE adj-IV', 'Bear CE adj-Delta', 'Bear CE adj-ltp',
                                         'Bear PE adj', 'Bear PE adj-IV', 'Bear PE adj-Delta', 'Bear PE adj-ltp',
                                         'Far ATM CE', 'Far ATM CE-IV', 'Far ATM CE-Delta', 'Far ATM CE-ltp', 'Far ATM PE',
                                         'Far ATM PE-IV', 'Far ATM PE-Delta', 'Far ATM PE-ltp', 'Far ATM sum ltp',
                                         'ATM CE', 'ATM CE-IV', 'ATM CE-Delta', 'ATM CE-ltp', 'ATM PE',
                                         'ATM PE-IV', 'ATM PE-Delta', 'ATM PE-ltp', 'ATM sum ltp',
                                         'MaxPain CE', 'MaxPain CE-IV', 'MaxPain CE-Delta', 'MaxPain CE-ltp', 'MaxPain PE',
                                         'MaxPain PE-IV', 'MaxPain PE-Delta', 'MaxPain PE-ltp', 'MaxPain sum ltp']])
        else:
            print("No Daily OI Data Received")
            sleep(30)

    except Exception as e:
        print(e)
        sys.stdout.flush()
        pass

    finally:
        print(datetime.now() - timenow, "Daily sheet written")


def update_weekly_oi(mp_df, timenow):
    try:
        if not mp_df.empty:
            gd.set_with_dataframe(gsh_weekly_oi_data,
                                  mp_df[['Time', 'PreviousClose', 'Open', 'SpotPrice', 'MaxPain', 'PCR', 'vix',
                                         'call_decay', 'put_decay', 'Live-ATM CE',
                                         'Live-ATM CE-IV', 'Live-ATM PE', 'Live-ATM PE-IV',
                                         'wvix', 'Wly CE', 'Wly CE-IV', 'Wly CE-Delta',
                                         'Wly CE-ltp', 'Wly PE', 'Wly PE-IV', 'Wly PE-Delta',
                                         'Wly PE-ltp', 'Wly CE-Maxpain', 'Wly CE-MP-IV',
                                         'Wly CE-MP-Delta', 'Wly CE-MP-ltp', 'Wly PE-Maxpain',
                                         'Wly PE-MP-IV', 'Wly PE-MP-Delta', 'Wly PE-MP-ltp',
                                         # 'Mly PE - I', 'Mly CE - I', 'Yearly PE - I', 'Yearly CE - I', 'Dly PE - II', 'Dly CE - II', 'Mly PE - II',
                                         # 'Mly CE - II', 'mvix',
                                         'MaxPain-II', 'adj vix', 'adj dvix']])
        else:
            print("No Weekly OI Data Received")
            sleep(30)

    except Exception as e:
        print(e)
        sys.stdout.flush()
        pass

    finally:
        print(datetime.now() - timenow, "Weekly sheet written")


def dump_to_sheet(df, timenow):
    try:
        # Write daily dump to to google sheets
        gd.set_with_dataframe(gsh_daily_dump, df)

    except Exception as e:
        print(e)
        sys.stdout.flush()
        pass

    finally:
        print(datetime.now() - timenow, "daily dump sheet written")


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
            try:
                df_file = pd.read_json(oi_filename, orient='index', compression='infer')
                df_read = pd.DataFrame(df_file)
            except Exception as error:
                print("Error reading oi data from json file, Error {0}".format(error))
                df_read = pd.DataFrame()

            try:
                mp_file = pd.read_json(mp_filename, orient='index', compression='infer')
                mp_df_read = pd.DataFrame(mp_file)
            except Exception as error:
                print("Error reading maxpain data from json file, Error {0}".format(error))
                mp_df_read = pd.DataFrame()

            df, mp_df, dailydata = fetch_oi(df_read, mp_df_read, dvix, wvix, mvix, vix, dayopen, prevclose, pchange)
            update_daily_oi(mp_df, timenow)
            update_weekly_oi(mp_df, timenow)
            # Do not Stop, all piviot Graph / Chart will fail to get data
            update_live_data(dailydata, timenow)

            if not df.empty:
                df['iV_pe'] = df['iV_pe'].replace(to_replace=0, method='bfill').values
                df['iV_ce'] = df['iV_ce'].replace(to_replace=0, method='bfill').values

                # Stopped Full dump to gsheet for performance improvement of gsheet
                # dump_to_sheet(df, timenow)

                # datetime(year, month, day, hour, minute, second, microsecond)
                dtnow = datetime.now()
                recentdtm = datetime(dtnow.year, dtnow.month, dtnow.day, dtnow.hour, dtnow.minute, dtnow.second)
                recenttime = dtnow.strftime('%H:%M')

                nextscan = dtnow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe)
                print("nextscan", nextscan, "RecentScan", recentdtm, "OI tm", dailydata.Time[0], "Recent tm", recenttime)
                print(nextscan < recentdtm, dailydata.Time[0] < recenttime)
                forwardscan = dtnow.replace(microsecond=0, second=0) + timedelta(minutes=timeframe + 1)
                # waitsecs = int(((forwardscan if nextscan < recentdtm or dailydata.Time[0] < recenttime else nextscan) - recentdtm).seconds)
                waitsecs = int(((forwardscan if nextscan < recentdtm or dailydata.Time[0] < recenttime else nextscan) - recentdtm).seconds)
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
