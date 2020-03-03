const Nomics = require('nomics');

console.log(Nomics)

const nomics = Nomics({
	apiKey: '040639f478bc2578a18b992f06b6e3da'
});

async function client() {
	const currencies = await nomics.currenciesTicker({
		ids: ['BTC', 'ETH'],
		interval: ['1d']
	});

	console.log(currencies);
}

client();