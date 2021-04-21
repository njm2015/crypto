DROP TABLE binance_algo_bid_ask;
DROP TABLE binance_xlm_bid_ask;
DROP TABLE binance_ada_bid_ask;


CREATE TABLE binance_algo_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;

CREATE TABLE binance_xlm_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;

CREATE TABLE binance_ada_bid_ask (
	ts TIMESTAMP,
	bidPrice DOUBLE PRECISION,
	bidQty DOUBLE PRECISION,
	askPrice DOUBLE PRECISION,
	askQty DOUBLE PRECISION
)
;
