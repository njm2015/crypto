import db_libs
import json
import logging
import os
import ssl
import sys
import websocket

from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

SYMBOL='BTC'
URL_PARAM = SYMBOL + 'USD'

logging.basicConfig(filename='./log/{}.log'.format(SYMBOL.lower()), level=logging.DEBUG)


dbConnection = "dbname='crypto' user='{}' host='localhost' password='{}'"

connectionpool = SimpleConnectionPool(1,5,dsn=dbConnection.format(os.environ.get('DBUSER'), os.environ.get('DBPWD')))

@contextmanager
def getcursor():
	conn = connectionpool.getconn()

	try:
		yield conn
	finally:
		connectionpool.putconn(conn)


def on_message(ws, message):
	message_json = json.loads(message)

	events = message_json['events']

	for event in events:
		with getcursor() as conn:
			cursor = conn.cursor()
			# print(db_libs.insert_str.format('btc', 'BTC', event['side'] == 'ask', event['price'], event['remaining']))
			try:
				if event['type'] == 'trade':
					cursor.execute(db_libs.trade_insert_str.format(SYMBOL.lower(), SYMBOL, event['makerSide'] == 'ask', event['price'], event['amount']))
				else:
					cursor.execute(db_libs.bid_ask_insert_str.format(SYMBOL.lower(), SYMBOL, event['side'] == 'ask', event['price'], event['remaining']))

				conn.commit()
			except:
				logging.error('Unexpected error: {}'.format(sys.exc_info()[0]))
				logging.error('event: {}'.format(json.dumps(event)))
				conn.rollback()


BTC_ws = websocket.WebSocketApp(
	'wss://api.gemini.com/v1/marketdata/{}?top_of_book=true'.format(URL_PARAM),
	on_message=on_message
)

print('running websocket for {}'.format(SYMBOL))
BTC_ws.run_forever(sslopt={'cert_reqs': ssl.CERT_NONE})
