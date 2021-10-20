import win32com.client
import pandas as pd
import time
import numpy as np


ExcelApp = win32com.client.GetActiveObject("Excel.Application")
ExcelApp.Visible = True


wb = ExcelApp.Workbooks.Open(r"F:\demo_file\sample.xlsx")  #change path as per ur sytem
ws = wb.Worksheets('Sheet1')
StartRow=2
while True :
    d = {'script' : ['HDFC','SBIN', 'ITC', 'BEL'],
     'price' : np.random.random_sample(size = 4)}

    df = pd.DataFrame(d)
    StartCol = 1
    ws.Range(ws.Cells(StartRow,StartCol),
             ws.Cells(StartRow+len(df.index)-1,
                      StartCol+len(df.columns)-1)
             ).Value = df.to_numpy()
    
    StartRow = StartRow+len(df.index)+2
    time.sleep(2)