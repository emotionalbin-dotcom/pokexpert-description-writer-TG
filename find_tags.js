const fs = require('fs');
const protobuf = require('protobufjs');

async function main() {
    const POGOProtos = await require('purified-protos')();
    const rawBuffer = fs.readFileSync('inventory_raw.bin');
    const response = POGOProtos.GetHoloholoInventoryOutProto.decode(rawBuffer);
    
    const obj = response.toJSON();
    if (obj.inventoryDelta && obj.inventoryDelta.inventoryItem) {
        let count = 0;
        for (const item of obj.inventoryDelta.inventoryItem) {
            const data = item.inventoryItemData;
            if (data && data.pokemonData) {
                const p = data.pokemonData;
                
                // Just test the first 5 pokemon
                if (count < 5) {
                    const pDataRaw = POGOProtos.PokemonDataProto.encode(p).finish();
                    const reader = protobuf.Reader.create(pDataRaw);
                    
                    let tags = [];
                    while (reader.pos < reader.len) {
                        const tag = reader.uint32();
                        const id = tag >>> 3;
                        const wireType = tag & 7;
                        tags.push(id);
                        reader.skipType(wireType);
                    }
                    
                    console.log(`Pokemon ID: ${p.pokemonId}, Tags: ${tags.join(',')}`);
                    count++;
                }
            }
        }
    }
}
main().catch(console.error);
