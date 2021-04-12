import datetime
import math
import numpy as np
import psycopg2
import os
import random

# conn = psycopg2.connect(
# 	host="localhost",
# 	database=os.environ.get('DBNAME'),
# 	user=os.environ.get('DBUSER'),
# 	password=os.environ.get('DBPWD')
# )

conn = psycopg2.connect(
	host="10.0.1.100",
	database='datager',
	user=os.environ.get('DBUSER'),
	password=os.environ.get('DBPWD')
)

cur = conn.cursor()

table_name = 'binance_btc_bid_ask'

query = '''
	SELECT ts FROM {} ORDER BY ts
'''.format(table_name)

cur.execute(query)
ts_arr = cur.fetchall()

interval_arr = []

for i, ts in enumerate(ts_arr):
	if i > 0:
		if ts[0] - ts_arr[i-1][0] > datetime.timedelta(seconds=1200):
			interval_arr[-1].append(ts_arr[i-1][0])
			interval_arr.append([ts[0]])
	else:
		interval_arr.append([ts[0]])

interval_arr[-1].append(ts_arr[-1][0])

for interval in interval_arr:
	print(interval)

for interval in interval_arr:
	print(interval[1] - interval[0])