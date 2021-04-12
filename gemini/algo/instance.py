import base64
import datetime, time
import hashlib
import hmac
import io
import json
import math
import numpy as np
import psycopg2
import os
import random
import redis
import requests

r = redis.Redis()
base_url = "https://api.sandbox.gemini.com"
gemini_api_key = os.environ.get('GEMINI_API_KEY')
gemini_api_secret = os.environ.get('GEMINI_API_SECRET').encode()
symbol = 'btcusd'
num_reqs = 0
print(num_reqs)

def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor

def round_decimals_up(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.ceil(number * factor) / factor

def get_order(client_id):

	global num_reqs

	endpoint = '/v1/order/status'
	url = base_url + endpoint

	t = datetime.datetime.now()
	payload_nonce = str(int(time.mktime(t.timetuple()) * 1000) + num_reqs)
	num_reqs += 1

	payload = {
		'request': '/v1/order/status',
		'nonce': payload_nonce,
		'client_order_id': client_id
	}

	encoded_payload = json.dumps(payload).encode()
	b64 = base64.b64encode(encoded_payload)
	signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

	request_headers = {
		'Content-Type': 'text/plain',
		'Content-Length': '0',
		'X-GEMINI-APIKEY': gemini_api_key,
		'X-GEMINI-PAYLOAD': b64,
		'X-GEMINI-SIGNATURE': signature,
		'Cache-Control': 'no-cache'
	}

	response = requests.post(url, data=None, headers=request_headers)
	return response.json()

def get_price():
	endpoint = '/v2/ticker/{}'.format(symbol)
	url = base_url + endpoint
	response = requests.get(url)
	return response.json()

class Algo:

	def __init__(self,
		instance_id,
		slots=100, 
		total_avail=100, 
		max_avail=1.0, 
		freq_sec=10, 
		max_idle_full_high=200, 
		max_idle_empty_high=200,
		max_idle_full_low=100,
		max_idle_empty_low=100, 
		maker=0.001, 
		undercut=0.0005,
		max_slope_perc=0.1,
		padding=0.02
	):
		#
		# slots: number of trading slots
		# total_avail: starting cash
		# max_avail: maximum cash in a slot before going into excess
		# freq_sec: trading frequency (seconds)
		# max_idle_full_high: upper bound on how long a slot can be full before selling
		# max_idle_empty_high: upper bound on how long a slot can be empty before buying
		# max_idle_full_low: lower bound on how long a slot can be full before selling
		# max_idle_empty_low: lower bound on how long a slot can be empty before buying
		# maker: maker/taker value of exchange (ex. binance-us: 0.075% ~ 0.00075)
		# undercut: if maker, how much under/over top of book will you ask/bid (ex. 0.1% over ~ 0.001)
		# max_slope_perc: used for determining whether the market trend is upward/downward or flat (currently unused)
		# padding: how much over break even a trade needs to be before it occurs
		#
		# Wallet array obj: [price, avail, btc, excess, idle_interval, pending < 0, num_trades]
 		#
		wallet = np.array([[-1.0, total_avail / slots, 0.0, 0.0, -1.0, 1.0, 0.0] for i in range(slots)])
		wallet.setflags(write=1)
		r.set('{}-wallet'.format(instance_id), wallet.tobytes())

		self.slots = slots
		self.instance_id = instance_id
		self.tick_num = 0
		self.freq_sec = freq_sec
		self.max_avail = max_avail
		self.max_idle_full_high = max_idle_full_high
		self.max_idle_empty_high = max_idle_empty_high
		self.max_idle_full_low = max_idle_full_low
		self.max_idle_empty_low = max_idle_empty_low
		self.maker = maker
		self.undercut = undercut
		self.max_slope_perc=max_slope_perc
		self.sell_log = []
		self.buy_log = []
		self.padding = padding
		self.external_excess = 0.0
		self.open_orders = set()

	def get_wallet(self):
		wallet_serialized = r.get('{}-wallet'.format(self.instance_id))
		self.wallet = np.array(np.frombuffer(wallet_serialized).reshape([self.slots, 7]))

	def set_wallet(self):
		r.set('{}-wallet'.format(self.instance_id), self.wallet.tobytes())

	def check_orders(self):

		global num_reqs

		active_orders = set()

		endpoint = '/v1/orders'
		url = base_url + endpoint

		t = datetime.datetime.now()
		payload_nonce = str(int(time.mktime(t.timetuple()) * 1000) + num_reqs)
		num_reqs += 1

		payload = {
			'request': '/v1/orders',
			'nonce': payload_nonce,
		}

		encoded_payload = json.dumps(payload).encode()
		b64 = base64.b64encode(encoded_payload)
		signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

		request_headers = {
			'Content-Type': 'text/plain',
			'Content-Length': '0',
			'X-GEMINI-APIKEY': gemini_api_key,
			'X-GEMINI-PAYLOAD': b64,
			'X-GEMINI-SIGNATURE': signature,
			'Cache-Control': 'no-cache'
		}

		response = requests.post(url, data=None, headers=request_headers)
		orders_arr = response.json()

		print(orders_arr)

		for order in orders_arr:
			active_orders.add(order['client_order_id'])

		for executed_order in self.open_orders.difference(active_orders):
			time.sleep(0.001)
			o = get_order(executed_order)
			print(o)
			if not o['is_cancelled']:
				self.buy_complete(price=o['avg_execution_price'], amt_purchased=o['executed_amount'])


	def tick(self, bid, ask):

		num_reqs = 0

		self.get_wallet()

		self.wallet[:,4] += 1

		min_s, is_start = self.min_slot(ask)
		print(min_s, is_start)
		for s in min_s:
			if self.should_buy(s, is_start, ask) and self.can_buy(s, ask):
				print('should_buy')
				self.buy(s, ask)
				self.wallet[s,4] = 0

		max_s = self.max_slot(bid)
		for s in max_s:
			if self.should_sell(s, bid) and self.can_sell(s, bid):
				self.sell(s, bid)
				self.wallet[s,4] = 0

		## Umcomment for market switching
		# if prev_pt is not None and abs(bid - prev_pt) / ((bid + prev_pt) / 2) > self.max_slope_perc:
		# 	# print(abs(bid - prev_pt) / ((bid + prev_pt) / 2))
		# 	mie = self.max_idle_empty_low
		# 	mif = self.max_idle_full_high
		# else:
		# 	mie = self.max_idle_empty_high
		# 	mif = self.max_idle_full_low


		## Uncomment to implement idle times
		mie = self.max_idle_empty_high
		# mif = self.max_idle_full_high

		max_idle_empty_s = self.max_idle_empty(mie)
		# max_idle_full_s = self.max_idle_full(mif)

		if max_idle_empty_s is not None:
			self.buy(max_idle_empty_s, ask)
			self.wallet[max_idle_empty_s,4] = 0

		# if max_idle_full_s is not None:
		# 	self.sell(max_idle_full_s, bid)
		# 	self.wallet[max_idle_full_s,4] = 0

		time.sleep(0.01)

		self.check_orders()

		self.set_wallet()


	def min_slot(self, ask):
		min_slot = [None, None]
		max_diff = 0.0

		for i, slot in enumerate(self.wallet):
			if slot[0] < 0:
				# start
				return [i], True

			if slot[2] > 1e-9:
				continue

			if slot[0] - ask > max_diff:
				min_slot.append(i)
				max_diff = slot[0] - ask

		# NOTE: min_slot will be None if all slots are filled
		if max_diff / ask > 0.0025:
			return min_slot[-2:], False
		else:
			return min_slot[-1:], False


	def max_slot(self, bid):
		max_slot = [None, None]
		max_diff = 0.0
		max_slot_2 = None

		for i, slot in enumerate(self.wallet):
			if slot[2] < 1e-9:
				continue

			if bid - slot[0] > max_diff:
				max_slot.append(i)
				max_diff = bid - slot[0]

		# NOTE: max_slot will be None if all slots are empty
		if max_diff / bid > 0.0025:
			return max_slot[-2:]
		else:
			return max_slot[-1:]


	def max_idle_empty(self, mie):
		max_idle = mie
		max_idle_i = None

		for i, row in enumerate(self.wallet):
			if row[0] is not None and row[2] < 1e-9 and row[4] > max_idle:
				max_idle = row[4]
				max_idle_i = i

		# NOTE: max_idle will be NULL if there are no empty slots or no slots > idle_max
		if random.random() < 0.8:
			return max_idle_i
		elif max_idle_i is not None:
			self.wallet[max_idle_i][4] = 0
			return None
		else:
			return None


	def max_idle_full(self, mif):
		max_idle = mif
		max_idle_i = None

		for i, row in enumerate(self.wallet):
			if row[0] is not None and row[2] > 1e-9 and row[4] > max_idle:
				max_idle = row[4]
				max_idle_i = i

		if random.random() < 0.8:
			return max_idle_i
		elif max_idle_i is not None:
			self.wallet[max_idle_i][4] = 0
			return None
		else:
			return None


	def should_buy(self, min_s, is_start, ask):
		if is_start:
			return True

		if min_s is None:
			return False

		return ask * (1 + self.maker + self.undercut) < self.wallet[min_s,0] * (1 - self.maker - self.undercut) * (1 - self.padding)


	def should_sell(self, max_s, bid):
		if max_s is None:
			return False

		try:
			return bid * (1 - self.maker - self.undercut) > self.wallet[max_s,0] * (1 + self.maker + self.undercut) * (1 + self.padding)
		except IndexError:
			print(max_s)


	def can_buy(self, max_s, bid):
		return self.wallet[max_s,1] * (1 - self.maker - self.undercut) > 0.5


	def can_sell(self, min_s, ask):
		return self.wallet[min_s,2] * (1 - self.maker - self.undercut) * ask > 0.5

	def buy(self, min_s, ask):
		print('buying...')

		global num_reqs

		btc = round_decimals_down(self.wallet[min_s,1] / ask, 6) * (1 - self.maker) * (1 - self.undercut)

		# send order request
		endpoint = '/v1/order/new'
		url = base_url + endpoint

		t = datetime.datetime.now()
		payload_nonce = str(int(time.mktime(t.timetuple()) * 1000) + num_reqs)
		num_reqs += 1

		payload = {
			'request': '/v1/order/new',
			'nonce': payload_nonce,
			'client_order_id': '{}-{}-{}'.format(self.instance_id, str(min_s), str(int(self.wallet[min_s][6]))),
			'symbol': symbol,
			'amount': btc, # wallet avail
			'price': str(ask),
			'side': 'buy',
			'type': 'exchange limit',
			'options': ['maker-or-cancel']
		}

		encoded_payload = json.dumps(payload).encode()
		b64 = base64.b64encode(encoded_payload)
		signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

		request_headers = {
			'Content-Type': 'text/plain',
			'Content-Length': '0',
			'X-GEMINI-APIKEY': gemini_api_key,
			'X-GEMINI-PAYLOAD': b64,
			'X-GEMINI-SIGNATURE': signature,
			'Cache-Control': 'no-cache'
		}

		response = requests.post(url, data=None, headers=request_headers)
		print(response)

		# add order to pending orders
		self.open_orders.add('{}-{}-{}'.format(self.instance_id, str(min_s), str(int(self.wallet[min_s][6]))))
		self.wallet[min_s,6] += 1
		self.wallet[min_s,5] = 1.0


	def sell(self, max_s, bid):
		# send order request

		# add order to pending orders
		pass

	def buy_complete(self, price, amt_purchased):
		# if self.wallet[min_s,1] 
		self.buy_log.append('{}:{}:{}'.format(self.wallet[min_s,0], ask, self.wallet[min_s,1]))
		# btc = round_decimals_down(self.wallet[min_s,1] / ask, 6) * (1 - self.maker) * (1 - self.undercut)
		self.wallet[min_s,1] -= round_decimals_up(amt_purchased * price, 2)
		self.wallet[min_s,0] = price
		self.wallet[min_s,2] = amnt_purchased


	def sell_complete(self, max_s, bid):
		self.sell_log.append('{}:{}:{}'.format(self.wallet[max_s,0], bid, self.wallet[max_s,2]))

		s_usd = round_decimals_down(self.wallet[max_s][2] * bid * (1 - self.maker) * (1 - self.undercut), 2)
		if s_usd > self.max_avail:
			# btc_for_max_avail = round_decimals_down(self.max_avail / (bid * (1 - self.maker) * (1 - self.undercut)), 8)
			self.wallet[max_s,3] += (s_usd - self.max_avail)
			self.wallet[max_s,1] = self.max_avail
			self.wallet[max_s,0] = bid
			self.wallet[max_s,2] = 0.0
		else:
			self.wallet[max_s,0] = bid
			self.wallet[max_s,1] = s_usd
			self.wallet[max_s,2] = 0.0


	def liquidate(self, ask):
		return self.wallet[:,1].sum() + self.wallet[:,2].sum() * ask + self.wallet[:,3].sum() + self.external_excess


	def rebalance(self):
		total_excess = self.wallet[:,3].sum()
		slot_addition = round_decimals_down(round_decimals_down(total_excess / 2, 2) / self.wallet.shape[0], 2)
		self.external_excess += total_excess - (slot_addition * self.wallet.shape[0])

		for slot in self.wallet:

			if slot[2] > 1e-9:
				# you have btc
				amount_paid = round_decimals_down(slot[0] * slot[2] * (1 + self.maker) * (1 + self.undercut), 2)
				amount_paid -= slot_addition
				new_price = (amount_paid / slot[2]) * (1 + self.maker) * (1 + self.undercut)
				slot[1] += slot_addition
				slot[0] = new_price
				slot[3] = 0.0
			else:
				slot[3] = slot_addition


# -----------------------------------------------------

algo = Algo(
	instance_id='1000',
	slots=10,
	total_avail=10, 
	max_avail=1.0, 
	padding=0.02, 
	maker=0.01,
	undercut=0.0
)

while True:
	price = get_price()
	# print(price['bid'], price['ask'])
	algo.tick(float(price['bid']), float(price['ask']))
	time.sleep(10)