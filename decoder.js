const fs = require('fs');

function decodeRaw(buffer, prefix = '') {
    let offset = 0;
    while (offset < buffer.length) {
        let tag = 0;
        let shift = 0;
        let b = 0;
        do {
            b = buffer[offset++];
            tag |= (b & 0x7f) << shift;
            shift += 7;
        } while (b & 0x80);

        const fieldNum = tag >> 3;
        const wireType = tag & 0x7;

        if (wireType === 0) { // Varint
            let val = 0;
            shift = 0;
            do {
                b = buffer[offset++];
                val |= (b & 0x7f) << shift;
                shift += 7;
            } while (b & 0x80);
            console.log(`${prefix}Field ${fieldNum}: Varint (${val})`);
        } else if (wireType === 1) { // 64-bit
            offset += 8;
            console.log(`${prefix}Field ${fieldNum}: 64-bit`);
        } else if (wireType === 2) { // Length-delimited
            let len = 0;
            shift = 0;
            do {
                b = buffer[offset++];
                len |= (b & 0x7f) << shift;
                shift += 7;
            } while (b & 0x80);
            
            console.log(`${prefix}Field ${fieldNum}: Length-delimited (${len} bytes)`);
            if (len > 0 && len <= buffer.length - offset) {
                const subBuf = buffer.slice(offset, offset + len);
                // Try to decode recursively if it looks like a message
                // Usually messages have valid tags. We just print hex for now
                console.log(`${prefix}  Hex: ${subBuf.slice(0, 16).toString('hex')}...`);
            }
            offset += len;
        } else if (wireType === 5) { // 32-bit
            offset += 4;
            console.log(`${prefix}Field ${fieldNum}: 32-bit`);
        } else {
            console.log(`${prefix}Unknown wire type ${wireType} at field ${fieldNum}`);
            break;
        }
    }
}

const data = fs.readFileSync('last_payload.bin');
console.log('--- RAW PROTOBUF DUMP ---');
decodeRaw(data);
