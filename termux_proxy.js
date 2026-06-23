const http = require('http');
const WebSocket = require('ws');
const axios = require('axios');

const PORT = 9001;
const REMOTE_URL = `https://pokexpert-description-writer-tg.onrender.com/hook/6040671411/PolygonX/PostProtos`;
const WS_REMOTE_URL = `wss://pokexpert-description-writer-tg.onrender.com/hook/6040671411`;

const server = http.createServer((req, res) => {
    if (req.method === 'POST') {
        let body = [];
        req.on('data', chunk => body.push(chunk));
        req.on('end', () => {
            const buffer = Buffer.concat(body);
            axios.post(REMOTE_URL, buffer, {
                headers: { 'Content-Type': 'application/octet-stream' }
            }).then(response => {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(response.data));
            }).catch(err => {
                console.error("HTTP Forwarding Error:", err.message);
                res.writeHead(500);
                res.end(err.message);
            });
        });
    } else {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: "ok", message: "Termux proxy is active" }));
    }
});

const wss = new WebSocket.Server({ noServer: true });

server.on('upgrade', (request, socket, head) => {
    wss.handleUpgrade(request, socket, head, (ws) => {
        console.log("Local WebSocket client connected, opening tunnel to cloud...");
        const remoteWs = new WebSocket(WS_REMOTE_URL);
        
        ws.on('message', (message) => {
            if (remoteWs.readyState === WebSocket.OPEN) {
                remoteWs.send(message);
            }
        });
        
        remoteWs.on('open', () => {
            console.log("Tunnel to cloud open!");
        });
        
        remoteWs.on('message', (message) => {
            ws.send(message);
        });
        
        ws.on('close', () => remoteWs.close());
        remoteWs.on('close', () => ws.close());
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Termux Proxy listening locally on http://127.0.0.1:${PORT}...`);
    console.log(`Forwarding to Render cloud...`);
});
