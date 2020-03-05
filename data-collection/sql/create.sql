CREATE TABLE crypto_10sec (
	symbol 	varchar(6),
	ts		timestamp without time zone,
	price	real,
	volume	bigint,
	PRIMARY KEY (symbol, ts)
);