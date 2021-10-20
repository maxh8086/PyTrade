#SANTANU MAJI
#TWITTER:-https://twitter.com/SANTANUMAJI1994
#YOUTUBE CHANNEL:-https://www.youtube.com/santanumaji
import pandas as pd
import glob
zip_file_list=glob.glob('*.zip')
total_zip_file=len(zip_file_list)
DATE=[]
OPEN=[]
HIGH=[]
LOW=[]
CLOSE=[]
COI=[]
for i in range(0,total_zip_file):
    df=pd.read_csv(zip_file_list[i])
    date=df['TIMESTAMP'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].iloc[0]
    openn=df['OPEN'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].iloc[0]
    high=df['HIGH'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].iloc[0]
    low=df['LOW'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].iloc[0]
    close=df['CLOSE'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].iloc[0]
    coi=df['OPEN_INT'][(df.INSTRUMENT=='FUTIDX') & (df.SYMBOL=="NIFTY")].sum()
    DATE.append(date)
    OPEN.append(openn)
    HIGH.append(high)
    LOW.append(low)
    CLOSE.append(close)
    COI.append(int(coi))
data={'DATE':DATE,'OPEN':OPEN,'HIGH':HIGH,'LOW':LOW,'CLOSE':CLOSE,'COI':COI}
ndf=pd.DataFrame(data)
ndf.to_csv('NIFTY.csv',index=False,mode='a') 
print("REPORT READY")



    