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

for i, m in enumerate(mewtwos):
    display_tags = []
    lines = m.split('\n')
    in_display = False
    d_level = 0
    b_level = 0
    for line in lines:
        if not in_display and re.search(r'^\s*36 \{', line):
            in_display = True
            d_level = b_level
        if in_display and b_level == d_level + 1:
            match = re.match(r'^\s*(\d+):', line)
            if match:
                display_tags.append((match.group(1), line.strip()))
        b_level += line.count('{') - line.count('}')
        if in_display and b_level == d_level:
            in_display = False
    if display_tags:
        print(f"Mewtwo {i+1} display tags: {[t[1] for t in display_tags]}")
