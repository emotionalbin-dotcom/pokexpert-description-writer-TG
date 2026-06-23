const express = require('express');
const http = require('http');
const fs = require('fs');
const WebSocket = require('ws');

const app = express();
const PORT = 9001;

const methodNames = {};
let POGOProtos;

app.use(express.raw({ type: '*/*', limit: '50mb' }));

app.all('/PolygonX/PostProtos', (req, res) => {
    const rawBody = req.body;
    
    if (!rawBody || rawBody.length === 0) {
        return res.sendStatus(400);
    }

    let contents = [];
    try {
        let offset = 0;
        while (offset < rawBody.length) {
            let tag = rawBody[offset++];
            if (tag !== 0x0A) break; 
            
            let len = 0, shift = 0, b;
            do {
                b = rawBody[offset++];
                len |= (b & 0x7f) << shift;
                shift += 7;
            } while (b & 0x80);
            
            let end = offset + len;
            let methodId = 0;
            let methodTag = rawBody[offset++];
            
            if (methodTag === 0x08) { 
                let mshift = 0, mb;
                do {
                    mb = rawBody[offset++];
                    methodId |= (mb & 0x7f) << mshift;
                    mshift += 7;
                } while (mb & 0x80);
            }
            
            let dataBuffer = null;
            let dataTag = rawBody[offset++];
            
            if (dataTag === 0x12 || dataTag === 0x1A) { 
                let dlen = 0, dshift = 0, db;
                do {
                    db = rawBody[offset++];
                    dlen |= (db & 0x7f) << dshift;
                    dshift += 7;
                } while (db & 0x80);
                
                dataBuffer = rawBody.slice(offset, offset + dlen);
            }
            
            offset = end;
            
            if (methodId > 0 && dataBuffer) {
                contents.push({ method: methodId, data: dataBuffer });
            }
        }
    } catch (e) {
        console.error("Binary unpacking error:", e);
    }

    // Process and decode each proto message
    for (let rawData of contents) {
        if (!rawData.data || !rawData.method) continue;

        const dataBuffer = rawData.data;
        const method = parseInt(rawData.method);

        try {
            const methodName = methodNames[method] || `UNKNOWN_METHOD_${method}`;
            
            // Only process raid-relevant methods
            if (methodName !== 'GYM_GET_INFO' && methodName !== 'JOIN_LOBBY' && methodName !== 'GET_RAID_DETAILS') {
                continue;
            }

            console.log(`\n========== ${methodName} ==========`);

            const className = methodName.split('_')
                .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
                .join('') + 'OutProto';

            const ProtoClass = POGOProtos[className];
            if (ProtoClass) {
                const decoded = ProtoClass.decode(dataBuffer);
                const obj = decoded.toJSON ? decoded.toJSON({ defaults: true }) : decoded;
                
                if (methodName === 'GYM_GET_INFO') {
                    console.log(`🏰 GYM: ${obj.name}`);
                    fs.writeFileSync('raid_state.json', JSON.stringify({ type: 'GYM_GET_INFO', data: obj }, null, 2));
                    const defenders = obj.gym_status_and_defenders?.pokemon_display?.length || 0;
                    console.log(`🛡️  Defenders: ${defenders}`);
                } 
                else if (methodName === 'JOIN_LOBBY' || methodName === 'GET_RAID_DETAILS') {
                    console.log(`⚔️  RAID LOBBY UPDATED`);
                    fs.writeFileSync('raid_state.json', JSON.stringify({ type: methodName, data: obj }, null, 2));
                    if (obj.lobby && obj.lobby.players) {
                        console.log(`👥 Players in Lobby: ${obj.lobby.players.length}`);
                    }
                    if (obj.raid_battle?.pokemon?.pokemon) {
                        console.log(`👹 Boss: ${obj.raid_battle.pokemon.pokemon.pokemon_id}`);
                    }
                }
            } else {
                console.log(`[!] Decoder class ${className} not found in POGOProtos.`);
            }
        } catch (err) {
            console.error(`Error decoding method ${method}:`, err.message);
        }
    }

    res.json({ status: "ok" });
});

app.all('*', (req, res) => {
    res.json({ status: "ok" });
});

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('MITM Client connected via WebSocket! Handshake successful.');
    
    // Spoof the backend init command so the game starts
    const fakeConfig = {
        type: "init",
        data: { assigned: true }
    };
    ws.send(JSON.stringify(fakeConfig));
});

async function startServer() {
    console.log("Loading POGOProtos definitions...");
    const initProtos = require('purified-protos');
    POGOProtos = await initProtos();
    
    for (const [key, value] of Object.entries(POGOProtos.Method)) {
        methodNames[value] = key.replace('METHOD_', '');
    }
    
    server.listen(PORT, '0.0.0.0', () => {
        console.log(`Sovereign Siphon Server listening on port ${PORT}...`);
    });
}
startServer();
