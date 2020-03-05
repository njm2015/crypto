const axios = require('axios');
const csv = require('csv-parser');
const fs = require('fs');

const apiKey = 'key=040639f478bc2578a18b992f06b6e3da&';
const tickerURL = 'https://api.nomics.com/v1/currencies/ticker?';
const interval = '&interval=1h';
const ids = 'ids=';


let symbolList = []

function generateURL() {
	return tickerURL + apiKey + ids + symbolList.join(',') + interval;
}


async function getTicker() {

	url = generateURL();

	axios.get(url)
		.then(res => {
			console.log(res.data);
		});
}



fs.createReadStream('../symbols.txt')
	.pipe(csv())
	.on('data', (row) => {
		symbolList.push(row.Symbol);
	})
	.on('end', () => {
		console.log('finished importing symbols....');
		setInterval(getTicker, 1000 * 10);
	});