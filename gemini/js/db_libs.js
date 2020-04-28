const bid_ask_create = (symbol) => `
CREATE TABLE gemini_${symbol}_bid_ask (
	ts			timestamp without time zone,
	symbol		varchar(6),
	type		boolean,
	price		real,
	reamining real
)
;
`


const trade_create = (symbol) => `
CREATE TABLE gemini_${symbol}_trade (
	ts 			timestamp without time zone,
	symbol		varchar(6),
	type		boolean,
	price		real,
	amount		real
)
;
`


const bid_ask_drop = (symbol) => `
DROP TABLE gemini_${symbol}_bid_ask
;
`


const trade_drop = (symbol) => `
DROP TABLE gemini_${symbol}_trade
;
`


const bid_ask_insert = (symbol, type, price, remaining) => `
INSERT INTO gemini_${symbol}_bid_ask (
	ts,
	symbol,
	type,
	price,
	remaining
) VALUES (
	CURRENT_TIMESTAMP,
	'${symbol}',
	${type},
	${price},
	${remaining}
)
;
`


const trade_insert = (symbol, ts, type, price, amount) => `
INSERT INTO gemini_${symbol}_trade (
	ts,
	symbol,
	type,
	price,
	amount
) VALUES (
	TO_TIMESTAMP(${ts}::double precision / 1000),
	'${symbol}',
	${type},
	${price},
	${amount}
)
;
`


module.exports = {
	bid_ask_create: bid_ask_create,
	trade_create: trade_create,
	bid_ask_drop: bid_ask_drop,
	trade_drop: trade_drop,
	bid_ask_insert: bid_ask_insert,
	trade_insert: trade_insert
}