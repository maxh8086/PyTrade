from flask import *
import pymysql
import sqlalchemy as db
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

engine = db.create_engine('mysql+pymysql://root:root@127.0.0.1:3306/market_data')
app = Flask(__name__)

@app.route('/')
def home():
    pe_strike_price = [14400,14300]
    ce_strike_price = [14400,14450]
    expirydate = '2021-01-14'
    table_ce= getTable(ce_strike_price,'oc_ce',expirydate)
    table_pe= getTable(pe_strike_price,'oc_pe',expirydate)
    final = pd.merge(table_pe,table_ce,how='left', on=['Time'],suffixes = ("_PE", "_CE"))
    fig = make_subplots(rows=2, cols=2,
                    specs=[[{"secondary_y": True}, {"secondary_y": True}],
                           [{"secondary_y": True}, {"secondary_y": True}]])

    # Top left
    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['OI_PE'],name="OI_PE"),
        row=1, col=1, secondary_y=False)

    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['OI_CE'], name="OI_CE"),
        row=1, col=1, secondary_y=True,
    )

    # Top right
    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['LTP_PE'], name="LTP_PE"),
        row=1, col=2, secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['LTP_CE'], name="LTP_CE"),
        row=1, col=2, secondary_y=True,
    )

    # Bottom left
    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['IV_PE'], name="IV_PE"),
        row=2, col=1, secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['IV_CE'], name="IV_CE"),
        row=2, col=1, secondary_y=True,
    )

    # Bottom right
    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['OI Change_PE'], name="OI Change_PE "),
        row=2, col=2, secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=final['Time'], y=final['OI Change_CE'], name="OI Change_CE"),
        row=2, col=2, secondary_y=True,
    )

    #fig.show()
    fig.write_html("templates/home.html")
    return render_template('home.html')


def getTable(strike_price,table_name,expirydate):
    
    table_df = pd.read_sql_table(table_name,con=engine)
    if expirydate is not None :
        table_df = table_df[table_df['Exp. Date'] == expirydate]
    if len(strike_price) > 0 :
        table_df = table_df[table_df['Strike Price'].isin(strike_price)]
    grouped = table_df.groupby(['Time']).agg({'LTP':'sum','OI':'sum','No.of contracts':'sum','OI Change':'sum','IV':'sum'}).reset_index()
    return grouped

if __name__ == '__main__':
    app.run(debug=True)