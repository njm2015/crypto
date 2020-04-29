const query = require('./db_libs')
const { Pool, Client } = require('pg');
const WebSocket = require('ws');
const winston = require('winston');

const SYMBOL = 'BCH';
const URL_PARAM = SYMBOL + 'USD';

const logger = winston.createLogger({
	level: 'info',
	format: winston.format.json(),
	defaultMeta: { service: 'user-service' },
	transports: [
		new winston.transports.File({ filename: './logs/error.log', level: 'error' }),
		new winston.transports.File({ filename: './logs/combined.log' })
	]
});


const pool = new Pool({
	user: process.env.DBUSER,
	host: 'localhost',
	database: 'crypto',
	password: process.env.DBPWD,
	port: 5432,
	max: 5
});


const socket = new WebSocket(`wss://api.gemini.com/v1/marketdata/${URL_PARAM}?top_of_book=true`);


socket.addEventListener('message', event => {

	msgData = JSON.parse(event.data);

	msgData.events.forEach(async c => {

		let q;

		if (c.reason !== 'initial') {

			if (c.type === 'trade') {
				q = query.trade_insert(
						SYMBOL.toLowerCase(),
						msgData.timestampms,
						c.makerSide === 'ask',
						c.price,
						c.amount
					);
			} else {
				q = query.bid_ask_insert(
						SYMBOL.toLowerCase(),
						c.side === 'ask',
						c.price,
						c.remaining
					);
			}

			pool
				.query(q)
				.catch(err => {
					logger.error(err.stack);
					logger.error(c);
					logger.error(q);
				});
		}

	});
});