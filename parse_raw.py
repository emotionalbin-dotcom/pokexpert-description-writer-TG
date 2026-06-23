import re

with open('inventory_decoded.txt', 'r') as f:
    lines = f.readlines()

pokemon_list = []
current = []
in_block = False
level = 0
block_level = 0

for line in lines:
    if not in_block and line.strip() == '1 {' and level == 2:
        in_block = True
        block_level = level
        current = []
        
    if in_block:
        current.append(line)
        
    level += line.count('{') - line.count('}')
    
    if in_block and level == block_level:
        in_block = False
        block_str = "".join(current)
        # Check if it's pokemon data (tag 2 = pokemon_id)
        if re.search(r'^\s*2:\s*\d+', block_str, re.MULTILINE):
            pokemon_list.append(block_str)

output = []
for p in pokemon_list:
    p_id_match = re.search(r'^\s*2:\s*(\d+)', p, re.MULTILINE)
    if not p_id_match: continue
    p_id = p_id_match.group(1)
    
    cp_match = re.search(r'^\s*3:\s*(\d+)', p, re.MULTILINE)
    cp = cp_match.group(1) if cp_match else "0"
    
    size_match = re.search(r'^\s*72:\s*(\d+)', p, re.MULTILINE)
    size = size_match.group(1) if size_match else "Normal"
    
    # PokemonDisplay is tag 36
    display_match = re.search(r'^\s*36\s*\{(.*?)\n\s*\}', p, re.MULTILINE | re.DOTALL)
    shiny = False
    background = "None"
    
    if display_match:
        d_block = display_match.group(1)
        if re.search(r'^\s*3:\s*1', d_block, re.MULTILINE):
            shiny = True
            
        loc_match = re.search(r'^\s*15\s*\{\s*\n\s*1:\s*(\d+)', d_block, re.MULTILINE | re.DOTALL)
        if loc_match:
            loc_card = loc_match.group(1)
            if loc_card == '246':
                background = 'Tokyo'
            else:
                background = f'ID {loc_card}'
                
    dynamax = bool(re.search(r'^\s*78\s*\{', p, re.MULTILINE))
    
    output.append({
        "pokemon_id": p_id,
        "cp": cp,
        "shiny": shiny,
        "background": background,
        "dynamax": dynamax,
        "size": size
    })

print(f"Total Pokemon parsed: {len(output)}")
mewtwos = [p for p in output if p['pokemon_id'] == '150']
for m in mewtwos:
    print(m)
