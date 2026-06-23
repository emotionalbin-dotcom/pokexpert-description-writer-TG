const express = require('express');
const http = require('http');
const fs = require('fs');
const WebSocket = require('ws');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 9001;

const methodNames = {};
let POGOProtos;

// Support multi-user: userId -> Map of pokemon
global.pokemonBags = {};

app.use(express.raw({ type: '*/*', limit: '50mb' }));

app.all(['/PolygonX/PostProtos', '/hook/:userId/PolygonX/PostProtos'], (req, res) => {
    const userId = req.params.userId || 'default';
    const rawBody = req.body;
    
    if (!rawBody || rawBody.length === 0) {
        return res.sendStatus(400);
    }

    // Initialize user's bag if not exists
    if (!global.pokemonBags[userId]) {
        global.pokemonBags[userId] = new Map();
    }
    const userBag = global.pokemonBags[userId];

    let contents = [];
    try {
        let offset = 0;
        while (offset < rawBody.length) {
            let tag = rawBody[offset++];
            if (tag !== 0x0A) break; // Field 1 Length-Delimited
            
            let len = 0, shift = 0, b;
            do {
                b = rawBody[offset++];
                len |= (b & 0x7f) << shift;
                shift += 7;
            } while (b & 0x80);
            
            let end = offset + len;
            let methodId = 0;
            let methodTag = rawBody[offset++];
            
            if (methodTag === 0x08) { // Field 1 Varint
                let mshift = 0, mb;
                do {
                    mb = rawBody[offset++];
                    methodId |= (mb & 0x7f) << mshift;
                    mshift += 7;
                } while (mb & 0x80);
            }
            
            let dataBuffer = null;
            let dataTag = rawBody[offset++];
            
            if (dataTag === 0x12 || dataTag === 0x1A) { // Field 2 or 3 Length-Delimited
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
        console.error(`[User: ${userId}] Binary unpacking error:`, e);
    }

    // Process and decode each proto message
    for (let rawData of contents) {
        if (!rawData.data || !rawData.method) continue;

        const dataBuffer = rawData.data;
        const method = parseInt(rawData.method);

        try {
            const methodName = methodNames[method] || `UNKNOWN_METHOD_${method}`;
            console.log(`\n========== [User: ${userId}] ${methodName} ==========`);
            
            // Convert METHOD_NAME to MethodNameOutProto
            if (methodName.startsWith('UNKNOWN')) {
                console.log(`[!] Cannot dynamically decode unknown method.`);
                continue;
            }

            const className = methodName.split('_')
                .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
                .join('') + 'OutProto';

            const ProtoClass = POGOProtos[className];
            if (ProtoClass) {
                const decoded = ProtoClass.decode(dataBuffer);
                const obj = decoded.toJSON ? decoded.toJSON({ defaults: true }) : decoded;
                
                const userDir = `data/${userId}`;
                if (!fs.existsSync(userDir)) {
                    fs.mkdirSync(userDir, { recursive: true });
                }

                // --- CUSTOM FILTERS & ELDORADO EXPORTER ---
                if (methodName === 'GET_PLAYER') {
                    console.log('👤 Syncing Player Data (Stardust, Poses)...');
                    fs.writeFileSync(`${userDir}/player_debug.json`, JSON.stringify(obj, null, 2));

                    // --- EXTRACT MEDALS (using correct purified-protos field names) ---
                    try {
                        const stats = (obj.player && obj.player.stats) || {};

                        // Gold thresholds for each medal (to filter only Gold+ / Platinum)
                        const GOLD_THRESHOLDS = {
                            kmWalked: 1000,
                            numPokemonCaptured: 5000,
                            pokeStopVisits: 2000,
                            numEvolutions: 200,
                            numEggsHatched: 500,
                            numRaidBattleWon: 2000,
                            numLegendaryBattleWon: 2000,
                            numGruntsDefeated: 2000,
                            numPokemonPurified: 1000,
                            numBestBuddies: 200,
                            sevenDayStreaks: 50,
                            uniquePokestopsVisited: 2000,
                            numTotalMegaEvolutions: 1000,
                            numWayfarerAgreement: 50,
                            numTrades: 2500,
                            numNpcCombatsWon: 200,
                            numPhotobombSeen: 200,
                            bigMagikarpCaught: 1000,
                            smallRattataCaught: 1000,
                        };

                        const PLATINUM_THRESHOLDS = {
                            kmWalked: 10000,
                            numPokemonCaptured: 50000,
                            pokeStopVisits: 50000,
                            numEvolutions: 2000,
                            numEggsHatched: 2500,
                            numRaidBattleWon: 10000,
                            numLegendaryBattleWon: 10000,
                            numGruntsDefeated: 10000,
                            numPokemonPurified: 5000,
                            numBestBuddies: 1000,
                            sevenDayStreaks: 500,
                            uniquePokestopsVisited: 10000,
                            numTotalMegaEvolutions: 2000,
                            numWayfarerAgreement: 500,
                            numTrades: 10000,
                            bigMagikarpCaught: 1000,
                            smallRattataCaught: 1000,
                        };

                        const MEDAL_LABELS = {
                            kmWalked: 'Jogger',
                            numPokemonCaptured: 'Collector',
                            pokeStopVisits: 'Backpacker',
                            numEvolutions: 'Scientist',
                            numEggsHatched: 'Breeder',
                            numRaidBattleWon: 'Champion (Raids)',
                            numLegendaryBattleWon: 'Battle Legend',
                            numGruntsDefeated: 'Hero (Rockets)',
                            numPokemonPurified: 'Purifier',
                            numBestBuddies: 'Best Buddy',
                            sevenDayStreaks: 'Ace Trainer',
                            uniquePokestopsVisited: 'Sightseer',
                            numTotalMegaEvolutions: 'Successor',
                            numWayfarerAgreement: 'Wayfarer',
                            numTrades: 'Gentleman',
                            numNpcCombatsWon: 'Veteran (PvP)',
                            numPhotobombSeen: 'Cameraman',
                            bigMagikarpCaught: 'Fisher',
                            smallRattataCaught: 'Youngster',
                        };

                        const gold_medals = [];
                        const platinum_medals = [];

                        for (const [field, label] of Object.entries(MEDAL_LABELS)) {
                            const val = stats[field] || 0;
                            const goldThresh = GOLD_THRESHOLDS[field] || 999999;
                            const platThresh = PLATINUM_THRESHOLDS[field] || 999999;
                            if (val >= platThresh) {
                                platinum_medals.push({ field, label, value: val, tier: 'PLATINUM' });
                            } else if (val >= goldThresh) {
                                gold_medals.push({ field, label, value: val, tier: 'GOLD' });
                            }
                        }

                        // Event badges (special event medals - GO Fest, Safari Zone etc)
                        const event_badges = stats.eventBadges || [];

                        const medalsOut = {
                            platinum: platinum_medals,
                            gold: gold_medals,
                            event_badges: event_badges,
                            raw_stats: {
                                kmWalked: stats.kmWalked || 0,
                                numPokemonCaptured: stats.numPokemonCaptured || 0,
                                pokeStopVisits: stats.pokeStopVisits || 0,
                                numRaidBattleWon: stats.numRaidBattleWon || 0,
                                numLegendaryBattleWon: stats.numLegendaryBattleWon || 0,
                                numGruntsDefeated: stats.numGruntsDefeated || 0,
                                numBestBuddies: stats.numBestBuddies || 0,
                                numTrades: stats.numTrades || 0,
                                numWayfarerAgreement: stats.numWayfarerAgreement || 0,
                            }
                        };
                        fs.writeFileSync(`${userDir}/medals_data.json`, JSON.stringify(medalsOut, null, 2));
                        console.log(`🏅 [User: ${userId}] Platinum: ${platinum_medals.length} | Gold: ${gold_medals.length} | Event: ${event_badges.length}`);
                    } catch(e) {
                        console.log(`[WARN] [User: ${userId}] Medal extraction failed:`, e.message);
                        fs.writeFileSync(`${userDir}/medals_data.json`, JSON.stringify({ platinum: [], gold: [], event_badges: [], error: e.message }, null, 2));
                    }
                    // --- END MEDALS ---

                    let playerData = {};
                    if (obj.player) {
                        if (obj.player.currency_balance) {
                            playerData.currency = obj.player.currency_balance;
                        }
                        if (obj.player.player_avatar_proto) {
                            playerData.avatar = obj.player.player_avatar_proto;
                        }
                        if (obj.player.creation_time_ms) {
                            playerData.creation_time = obj.player.creation_time_ms;
                        }
                    } else if (obj.player_data) {
                        if (obj.player_data.currency_balance) playerData.currency = obj.player_data.currency_balance;
                        if (obj.player_data.player_avatar_proto) playerData.avatar = obj.player_data.player_avatar_proto;
                        if (obj.player_data.avatar) playerData.avatar = obj.player_data.avatar;
                    }
                    
                    fs.writeFileSync(`${userDir}/player_raw.json`, JSON.stringify(playerData, null, 2));
                    console.log(`✅ [User: ${userId}] Dumped player data to player_raw.json`);
                }
                else if (methodName === 'GET_HOLOHOLO_INVENTORY') {
                    console.log(`🔄 [User: ${userId}] Syncing Inventory for Eldorado Exporter...`);
                    
                    if (obj.inventory_delta && obj.inventory_delta.inventory_item) {
                        let newListings = 0;
                        let items = {};
                        let level = "???";
                        let xp = "???";
                        let max_xp = -1;

                        obj.inventory_delta.inventory_item.forEach(item => {
                            if (!item.inventory_item_data) return;
                            const iid = item.inventory_item_data;

                            // 1. Store Pokemon
                            if (iid.pokemon) {
                                const p = iid.pokemon;
                                if (p.is_egg || !p.pokemon_id) return;
                                userBag.set(p.id || p.pokemon_id + Math.random(), p);
                                newListings++;
                            }

                            // 2. Store Items
                            if (iid.item) {
                                const it = iid.item;
                                const itemId = it.item_id || it.item;
                                const count = it.count || 0;
                                if (itemId) {
                                    items[itemId] = (items[itemId] || 0) + count;
                                }
                            }

                            // 3. Store Player Stats (Level & XP)
                            if (iid.player_stats) {
                                const ps = iid.player_stats;
                                const exp = parseInt(ps.experience || ps.xp || 0);
                                if (exp > max_xp) {
                                    max_xp = exp;
                                    level = ps.level || level;
                                    xp = exp;
                                }
                            }
                        });

                        if (Object.keys(items).length > 0) {
                            fs.writeFileSync(`${userDir}/items_data.json`, JSON.stringify(items, null, 2));
                        }
                        if (level !== "???" || xp !== "???") {
                            fs.writeFileSync(`${userDir}/level_xp.json`, JSON.stringify({ level, xp }, null, 2));
                        }
                        
                        if (newListings > 0) {
                            // Write fully decoded inventory raw JSON
                            fs.writeFileSync(`${userDir}/inventory_raw.json`, JSON.stringify(Array.from(userBag.values()), null, 2));

                            // --- EXTRACT POKEDEX & SHINY SPECIES ---
                            let pokedexUnique = 0;
                            const shinySpeciesSet = new Set();
                            obj.inventory_delta.inventory_item.forEach(item => {
                                if (!item.inventory_item_data) return;
                                const iid = item.inventory_item_data;
                                // Pokedex entries
                                if (iid.pokedex_entry) {
                                    const entry = iid.pokedex_entry;
                                    if ((entry.times_captured || entry.times_encountered || entry.pokemon_id_for_pokedex_entry) > 0
                                        || entry.pokemon_id_for_pokedex_entry) {
                                        pokedexUnique++;
                                    }
                                }
                                // Count unique shiny species from pokemon bag
                                if (iid.pokemon_data || iid.pokemon) {
                                    const p = iid.pokemon_data || iid.pokemon;
                                    if (!p.is_egg && p.pokemon_id && p.pokemon_display && p.pokemon_display.shiny) {
                                        shinySpeciesSet.add(p.pokemon_id);
                                    }
                                }
                            });

                            const pokedexData = {
                                unique_caught: pokedexUnique,
                                shiny_species: shinySpeciesSet.size,
                                shiny_species_list: Array.from(shinySpeciesSet)
                            };
                            fs.writeFileSync(`${userDir}/pokedex_data.json`, JSON.stringify(pokedexData, null, 2));
                            console.log(`📖 [User: ${userId}] Pokedex: ${pokedexUnique} unique, ✨ ${shinySpeciesSet.size} shiny species`);
                            // --- END POKEDEX ---

                            // --- EXTRACT SPECIAL RESEARCH ---
                            try {
                                const specialResearch = [];
                                const fieldResearch = [];
                                obj.inventory_delta.inventory_item.forEach(item => {
                                    if (!item.inventory_item_data) return;
                                    const iid = item.inventory_item_data;
                                    const quest = iid.quest || iid.special_research || iid.quest_master;
                                    if (!quest) return;
                                    
                                    const title = quest.quest_context || quest.title || quest.template_id || 'Unknown Research';
                                    const status = quest.status || quest.quest_status || 'UNKNOWN';
                                    const completedSteps = quest.goal ? (quest.goal.filter ? quest.goal.filter(g => g && g.current >= g.target).length : 0) : 0;
                                    
                                    const isSpecial = !!(quest.story_quest_id || quest.special_research_id || (quest.quest_rewards && quest.quest_rewards.length > 1));
                                    
                                    const entry = {
                                        title: typeof title === 'string' ? title.replace(/_/g, ' ') : JSON.stringify(title),
                                        status: typeof status === 'string' ? status : JSON.stringify(status),
                                        completed_steps: completedSteps,
                                        rewards: quest.quest_rewards ? quest.quest_rewards.length : 0
                                    };
                                    
                                    if (isSpecial) specialResearch.push(entry);
                                    else fieldResearch.push(entry);
                                });
                                
                                fs.writeFileSync(`${userDir}/research_data.json`, JSON.stringify({ special_research: specialResearch, field_research: fieldResearch }, null, 2));
                                console.log(`🔬 [User: ${userId}] Research: ${specialResearch.length} special, ${fieldResearch.length} field tasks`);
                            } catch(e) {
                                console.log(`[WARN] [User: ${userId}] Research extraction failed:`, e.message);
                                fs.writeFileSync(`${userDir}/research_data.json`, JSON.stringify({ special_research: [], field_research: [], error: e.message }, null, 2));
                            }
                            // --- END SPECIAL RESEARCH ---

                            console.log(`✅ [User: ${userId}] Dumped raw JSON data to inventory_raw.json for Python processing!`);
                            
                            // Trigger Python bot to process the data
                            console.log(`🚀 [User: ${userId}] Triggering Python bot to generate description...`);
                            axios.post('http://127.0.0.1:5000/internal/trigger_generate', { userId })
                                .then(response => {
                                    console.log(`[User: ${userId}] Python bot response:`, response.data);
                                })
                                .catch(err => {
                                    console.error(`[User: ${userId}] Error calling Python bot:`, err.message);
                                });
                        }
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

// Polygon sometimes sends a test ping to the root URL or with a GET request
app.all('*', (req, res) => {
    console.log(`[Ping] Polygon requested: ${req.method} ${req.path}`);
    res.json({ status: "ok" });
});

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('Polygon connected via WebSocket! Handshake successful.');
    
    // Spoof the backend init command so Polygon stops looping and starts the game
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
        console.log(`Live Protobuf parser & WebSocket listening on port ${PORT}...`);
    });
}
startServer();
