const axios = require('axios');
const POGOProtos = require('pogo-protos');

const ZYGARDE_URL = 'http://127.0.0.1:8080/dump/dl';

console.log('--- ZYGARDE LIVE POLLER ---');
console.log('Polling Zygarde for live protos every 2 seconds...');
console.log('Waiting for game to open and Zygarde to start hosting data...\n');

let lastSize = 0;

setInterval(async () => {
    try {
        const response = await axios.get(ZYGARDE_URL, { 
            responseType: 'arraybuffer', 
            timeout: 1000 
        });
        
        const dataBuffer = response.data;
        
        if (dataBuffer && dataBuffer.length > 0 && dataBuffer.length !== lastSize) {
            console.log(`\n[+] Zygarde dumped new data! Size: ${dataBuffer.length} bytes`);
            lastSize = dataBuffer.length;
            
            // Just print the raw hex of the first 50 bytes so we can see what Zygarde gives us
            console.log("Raw Data snippet:", dataBuffer.slice(0, 50).toString('hex'));
        }
    } catch (err) {
        // If Zygarde isn't running or port isn't open, suppress error so we don't spam terminal
        // console.error(err.message);
    }
}, 2000);
