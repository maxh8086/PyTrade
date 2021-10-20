#!/usr/bin/env python
# coding: utf-8

# In[1]:


pip install pandas_ta


# In[1]:


import pandas as pd
import pandas_ta as ta


# In[2]:


df = pd.read_csv('F:/demo_file/kite_ieod_1.csv')


# In[4]:


ta.sma(df["Close"], length=10)


# In[9]:


df['sup'] = ta.supertrend(high=df['High'], low=df['Low'], close=df['Close'], period=7, multiplier=3)['SUPERT_7_3.0']


# In[13]:


df.head(45)


# In[20]:


df['Buy_Signal'] = 0
df['Sell_Signal'] = 0
n =7
for i in range(n,len(df)):
    if df['Close'][i-1]<= df['sup'][i-1] and df['Close'][i] > df['sup'][i]:
        df['Buy_Signal'][i] = 1
    if df['Close'][i-1] >= df['sup'][i-1] and df['Close'][i] < df['sup'][i]:
        df['Sell_Signal'][i] = 1
      


# In[25]:


df[ (df['Buy_Signal'] > 0) | (df['Sell_Signal'] > 0) ]


# In[ ]:




