const axios = require('axios');
const csv = require('csv-parser');
const fs = require('fs');
const { Pool, Client } = require('pg');
const winston = require('winston');
const moment = require('moment');

const apiKey = 'key=040639f478bc2578a18b992f06b6e3da&';
const tickerURL = 'https://api.nomics.com/v1/currencies/ticker?';
const interval = '&interval=1h';
const ids = 'ids=';

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

insertQuery = `
	INSERT INTO crypto_10sec (
		symbol,
		ts,
		price,
		volume
	) VALUES ($1, TO_TIMESTAMP($2, 'DD-MM-YYYY HH24:MI:SS'), $3, $4);
`

let symbolList = []

function generateURL() {
	return tickerURL + apiKey + ids + symbolList.join(',') + interval;
}


async function getTicker() {

	url = generateURL();

	axios.get(url)
		.then(async res => {
			timestamp = moment().format('DD-MM-YYYY HH:mm:ss');
			logger.info(`${timestamp} -- Received ${res.data.length} rows from nomics...`);
			try {
				pool.connect((err, client, done) => {
					if (err) logger.error(err.stack);

					res.data.forEach(async c => {
						client.query(insertQuery, [
							c.symbol,
							timestamp,
							parseFloat(c.price),
							parseFloat(c['1h'].volume)
						]);
					});

					done();
				});

			} catch (err) {
				logger.error(err.stack);
			}
		});
}


async function insert(values) {
	try {
		const res = await client.query(insertQuery, values);
		console.log(res);
	} catch (err) {
		console.log(err.stack);
	}

	try {
		await client.end();
	} catch (err) {
		console.log(err.stack);
	}
}


fs.createReadStream('../symbols.txt')
	.pipe(csv())
	.on('data', (row) => {
		symbolList.push(row.Symbol);
	})
	.on('end', () => {
		logger.info('finished importing symbols....');
		setInterval(getTicker, 1000 * 10);
	});