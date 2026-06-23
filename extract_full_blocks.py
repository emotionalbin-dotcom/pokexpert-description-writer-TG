import re
with open('inventory_decoded.txt', 'r') as f:
    lines = f.readlines()

mewtwos = []
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
        if re.search(r'^\s*2:\s*150\s*$', block_str, re.MULTILINE):
            mewtwos.append(block_str)

shiny_tokyo = []
for m in mewtwos:
    # 3: 1 means shiny
    if re.search(r'^\s*3:\s*1\s*$', m, re.MULTILINE):
        shiny_tokyo.append(m)

with open('shiny_mewtwos.txt', 'w') as f:
    for m in shiny_tokyo:
        f.write("=== MEWTWO ===\n" + m + "\n\n")
        
print(f"Found {len(shiny_tokyo)} true shiny Mewtwos.")
