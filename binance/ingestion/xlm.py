import os
# import psycopg2
import requests
import sqlite3
import time

# conn = psycopg2.connect(
# 	host="localhost",
# 	database=os.environ.get('DBNAME'),
# 	user=os.environ.get('DBUSER'),
# 	password=os.environ.get('DBPWD')
# )

headers = {'X-MBX-APIKEY': os.environ.get('BINANCEKEY')}
params = {'symbol': 'XLMUSDT'}

while True:

	conn = sqlite3.connect('crypto.db')

	res = requests.get('https://api.binance.us/api/v3/ticker/bookTicker', headers=headers, params=params)

	res_json = res.json()

	cursor = conn.cursor()
	cursor.execute('''
		INSERT INTO binance_xlm_bid_ask (
			ts,
			bidprice,
			bidqty,
			askprice,
			askqty
		) VALUES (
			datetime('now'),
			?,
			?,
			?,
			?
		)
	''', [
		res_json.get('bidPrice'),
		res_json.get('bidQty'), 
		res_json.get('askPrice'), 
		res_json.get('askQty')
	])

	conn.commit()
	cursor.close()

	time.sleep(10)