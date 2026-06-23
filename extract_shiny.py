with open('inventory_decoded.txt', 'r') as f:
    lines = f.readlines()

shiny_mewtwos = []

current_block = []
level = 0
in_block = False
block_level = 0
is_mewtwo = False
is_shiny = False

for line in lines:
    braces = line.count('{') - line.count('}')
    
    # We want to capture the `1 {` that is directly under `3 {` ? 
    # Actually, let's just capture ANY block that starts with `1 {` and see if it has Mewtwo
    if not in_block and line.strip() == '1 {':
        in_block = True
        block_level = level
        current_block = []
        is_mewtwo = False
        is_shiny = False
        
    if in_block:
        current_block.append(line)
        if re.search(r'^\s*2:\s*150\s*$', line):
            is_mewtwo = True
        if re.search(r'^\s*6:\s*1\s*$', line):
            is_shiny = True
            
    level += braces
    
    if in_block and level == block_level:
        in_block = False
        if is_mewtwo and is_shiny:
            shiny_mewtwos.append("".join(current_block))

print(f"Found {len(shiny_mewtwos)} shiny Mewtwos!")
for i, m in enumerate(shiny_mewtwos):
    print(f"\n--- Shiny Mewtwo {i+1} ---")
    print(m)
