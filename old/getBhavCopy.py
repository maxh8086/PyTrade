# Fetching NIFTY futures data from bhavcopy files and storing it into a DataFrame

dates = [str(x) if x >= 10 else '0' + str(x) for x in range(1, 32)]
months = [str(x) if x >= 10 else '0' + str(x) for x in range(1, 13)]
years = [2020]

data = pd.DataFrame(columns=['<ticker>', '<date>', '<open>', '<high>', '<low>', '<close>', '<volume>', '<o/i>'])
df = pd.DataFrame()

for year in years :
    for month in months :
        for date in dates :
            filename = f'{year}-{month}-{date}-NSE-FO.txt'
            try :
                df = pd.read_csv(filename)
                data = data.append(df.iloc[3 :6], ignore_index=True)
            except :
                pass

# Keeping only the required columns and renaming them
data = data[['<ticker>', '<date>', '<close>', '<volume>', '<o/i>']]
data.columns = ['ticker', 'date', 'close', 'volume', 'oi']

# converting date column elements into datetime object from integers and making the Date as the index
Date = []
a = data['date']

for i in range(len(a)) :
    c = str(a[i])
    b = datetime(year=int(c[0 :4]), month=int(c[4 :6]), day=int(c[6 :8]))
    Date.append(b)

data['Date'] = Date
data.set_index('Date', drop=True, inplace=True)
data.drop(['date'], axis=1, inplace=True)

data.head()