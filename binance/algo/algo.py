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
	host='10.0.1.100',
	database='datager',
	user=os.environ.get('DBUSER'),
	password=os.environ.get('DBPWD')
)


cur = conn.cursor()

# tbl_names = ['binance_ltc_bid_ask']
# tbl_names = ['binance_eth_bid_ask']
tbl_names = ['binance_btc_bid_ask']
# tbl_names = ['binance_test_bid_ask']
rows = []

for tbl in tbl_names:
	# cur.execute('SELECT bidprice, bidqty, askprice, askqty FROM {} ORDER BY ts'.format(tbl))
	cur.execute("SELECT bidprice, bidqty, askprice, askqty FROM {} WHERE ts > '2021-01-25 02:11:36' order by ts".format(tbl))
	rows.append(cur.fetchall())

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

class Algo:

	def __init__(self, 
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
		# Wallet array obj: [price, avail, btc, excess, idle_interval]
 		#
		self.wallet = np.array([[None, total_avail / slots, 0.0, 0.0, -1] for i in range(slots)])
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

	def tick(self, bid, ask, prev_pt):

		self.wallet[:,4] += 1

		min_s, is_start = self.min_slot(ask)
		for s in min_s:
			if self.should_buy(s, is_start, ask) and self.can_buy(s, ask):
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
		mif = self.max_idle_full_high

		max_idle_empty_s = self.max_idle_empty(mie)
		max_idle_full_s = self.max_idle_full(mif)

		if max_idle_empty_s is not None:
			self.buy(max_idle_empty_s, ask)
			self.wallet[max_idle_empty_s,4] = 0

		if max_idle_full_s is not None:
			self.sell(max_idle_full_s, bid)
			self.wallet[max_idle_full_s,4] = 0


	def min_slot(self, ask):
		min_slot = [None, None]
		max_diff = 0.0

		for i, slot in enumerate(self.wallet):
			if slot[0] == None:
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
		return self.wallet[max_s,1] * (1 - self.maker - self.undercut) > 10.0


	def can_sell(self, min_s, ask):
		return self.wallet[min_s,2] * (1 - self.maker - self.undercut) * ask > 10.0


	def buy(self, min_s, ask):
		# if self.wallet[min_s,1] 
		self.buy_log.append('{}:{}:{}'.format(self.wallet[min_s,0], ask, self.wallet[min_s,1]))
		btc = round_decimals_down(self.wallet[min_s,1] / ask, 6) * (1 - self.maker) * (1 - self.undercut)
		self.wallet[min_s,1] -= round_decimals_up(btc * ask, 2)
		self.wallet[min_s,0] = ask
		self.wallet[min_s,2] = btc


	def sell(self, max_s, bid):
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


	def liquidate(self, bid):
		# You can sell immediately at bid
		return self.wallet[:,1].sum() + self.wallet[:,2].sum() * bid + self.wallet[:,3].sum() + self.external_excess


	def rebalance(self):

		print('rebalancing....')
		print(self.wallet[:,3].sum())

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
				## New code
				# amount_sold = slot[0] * 
				slot[3] = slot_addition


# -----------------------------------------------------

# idle_times = [20, 50, 100, 200, 400, 500, 800, 1000, 2000, 2500, 3000, 3500, 4000, 4500]
# idle_times = [10000]

# for idle in idle_times:

# 	print(idle)
algo = Algo(
	slots=100,
	total_avail=1500, 
	max_avail=15.0, 
	maker=0.00075, 
	padding=0.02, 
	undercut=0.0,
	max_idle_full_high=8640 * 3,
	max_idle_empty_high=8640 * 3
)

for i, row in enumerate(rows[0]):
	if i > 60:
		algo.tick(row[0], row[2], rows[0][i-60][0])
	else:
		algo.tick(row[0], row[2], None)

	if i > 0 and i % (8640 * 1) == 0:
		algo.rebalance()

# print(algo.wallet.shape)
# for row in algo.wallet:
# 	print(row[:4])

print('liquidity:\t {}'.format(algo.liquidate(rows[0][-1][0])))
print('excess:\t\t {}'.format(algo.wallet[:,3].sum()))
# print(algo.wallet[:,3].sum() * ask)
print('buy & hold amt:\t {}'.format(((1500 / rows[0][0][2]) * 0.999) * rows[0][-1][0] * 0.999))
print('# Buys: \t{}'.format(len(algo.buy_log)))
print('# Sells: \t{}'.format(len(algo.sell_log)))
print('External Excess:\t{}'.format(algo.external_excess))
print('-------------------------------------')