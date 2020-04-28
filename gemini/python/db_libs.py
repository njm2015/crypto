bid_ask_create_str = '''
CREATE TABLE gemini_{}_bid_ask (
	ts 			timestamp without time zone, 	-- date of insert
	symbol 		varchar(6),						-- symbol for currency
	type 		boolean,						-- false -> bid; true -> ask
	price 		real,							-- currency price
	remaining 	real
)
;
'''

trade_create_str = '''
CREATE TABLE gemini_{}_trade (
	ts 			timestamp without time zone,	-- date of insert
	symbol		varchar(6),						-- symbol for currency
	type		boolean,						-- false -> bid; true -> ask
	price		real,							-- execution price
	amount		real							-- trade quantity
)
;
'''


bid_ask_drop_str = '''
DROP TABLE gemini_{}_bid_ask
;
'''

trade_drop_str = '''
DROP TABLE gemini_{}_trade
;
'''


bid_ask_insert_str = '''
INSERT INTO gemini_{}_bid_ask (
	ts,
	symbol,
	type,
	price,
	remaining
) VALUES (
	CURRENT_TIMESTAMP, '{}', {}, {}, {}
)
;
'''

trade_insert_str = '''
INSERT INTO gemini_{}_trade (
	ts,
	symbol,
	type,
	price,
	amount
) VALUES (
	CURRENT_TIMESTAMP, '{}', {}, {}, {}
)
;
'''


if __name__ == '__main__':
	import os
	import psycopg2
	import sys

	symbol = sys.argv[1]
	print('resetting {}...'.format(symbol))

	connect_dsn = "dbname='crypto' user='{}' host='localhost' password='{}'".format(os.environ.get('DBUSER'), os.environ.get('DBPWD'))

	try:
		try:
			conn = psycopg2.connect(connect_dsn)
		except:
			print('unable to create db connection')

		cur = conn.cursor()

		# bid-ask tables

		try:
			# db doesn't exist
			cur.execute(bid_ask_drop_str.format(symbol))
		except:
			conn.rollback()
			print(sys.exc_info()[0])
			print(87)


		try:
			# db doesn't exist
			cur.execute(bid_ask_create_str.format(symbol))
		except:
			print(sys.exc_info()[0])
			print(95)

		conn.commit()

		# trade tables

		try:
			# db doesn't exist
			cur.execute(trade_drop_str.format(symbol))
		except:
			conn.rollback()
			print(sys.exc_info()[0])
			print(105)

		try:
			# db doesn't exist
			cur.execute(trade_create_str.format(symbol))
		except:
			print(sys.exc_info()[0])
			print(112)

		
		conn.commit()
		conn.close()

	except:
		conn.rollback()
		conn.close()
		print(sys.exc_info()[0])



