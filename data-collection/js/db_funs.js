const { Client } = require('pg');

const client = new Client({
	user: process.env.DBUSER,
	host: 'localhost',
	database: 'crypto',
	password: process.env.DBPWD,
	port: 5432
});

client.connect()

createTableQuery = `
	CREATE TABLE crypto_10sec (
		symbol 	varchar(6),
		ts		timestamp without time zone,
		price	real,
		volume	float8,
		PRIMARY KEY (symbol, ts)
	);
`

insertQuery = `
	INSERT INTO crypto_10sec (
		symbol,
		ts,
		price,
		volume
	) VALUES ($1, $2, $3, $4);
`

dropQuery = `
	DROP TABLE crypto_10sec;
`

selectAllQuery = `
	SELECT * 
	FROM crypto_10sec;
`

async function createTable() {
	try {
		const res = await client.query(createTableQuery);
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

async function insert(client, values) {
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

async function queryAll() {
	try {
		const res = await client.query(selectAllQuery);
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

async function resetTable() {
	try {
		const res = await client.query(dropQuery);
		console.log(res);
	} catch (err) {
		console.log(err.stack);
	}

	try {
		const res = await client.query(createTableQuery);
		console.log(res);
	} catch (err) {
		console.log(err.stack);
	}

	// try {
	// 	await client.end();
	// } catch (err) {
	// 	console.log(err.stack);
	// }
}

resetTable();
// insert(['BTK', '2020-03-05T00:00:00Z', 0.00458624, 538.6]);
setTimeout(queryAll, 2000);