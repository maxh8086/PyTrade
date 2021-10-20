import os
import sys
from time import sleep
from datetime import datetime, time, timedelta, date

path = os.path.join("py.log")
sys.stdout = open(path, 'w')
print(datetime.now(), 'this is python file')
sys.stdout.close()
