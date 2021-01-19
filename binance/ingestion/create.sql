DROP TABLE binance_ltc_bid_ask;
DROP TABLE binance_eth_bid_ask;
DROP TABLE binance_btc_bid_ask;


CREATE TABLE binance_ltc_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;

CREATE TABLE binance_btc_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;

CREATE TABLE binance_eth_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;

GRANT ALL PRIVILEGES ON binance_ltc_bid_ask TO datager;
GRANT ALL PRIVILEGES ON binance_eth_bid_ask TO datager;
GRANT ALL PRIVILEGES ON binance_btc_bid_ask TO datager;
