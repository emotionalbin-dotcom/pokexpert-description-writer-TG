const express = require('express');
const app = express();

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.text({ type: '*/*', limit: '50mb' }));

app.all('*', (req, res) => {
    console.log(`\n\n--- INCOMING ATLAS REQUEST to ${req.path} ---`);
    console.log('Headers:', req.headers);
    
    let body = req.body;
    if (Buffer.isBuffer(body)) {
        console.log('Body is RAW BINARY (length):', body.length);
        console.log('First 50 bytes:', body.slice(0, 50).toString('hex'));
    } else if (typeof body === 'object') {
        console.log('Body is JSON object:', JSON.stringify(body).substring(0, 500) + '...');
    } else if (typeof body === 'string') {
        console.log('Body is STRING (length):', body.length);
        console.log('First 200 chars:', body.substring(0, 200));
    }

    if (body && body.type === 'get_account') {
        console.log("--> Faking RDM Account Response...");
        return res.json({
            username: "D_20PASSES_06",
            password: "Kartik@123",
            first_warning_timestamp: 0,
            failed_timestamp: 0,
            failed: null,
            level: 30,
            spins: 0,
            creation_timestamp: Date.now() / 1000,
            warn: null,
            warn_expire_timestamp: 0,
            warn_message_acknowledged: true,
            suspended_message_acknowledged: true,
            was_suspended: false,
            banned: false
        });
    }

    res.status(200).send('OK');
});

const PORT = 9002;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Atlas Sniffer] Listening on port ${PORT}...`);
});
