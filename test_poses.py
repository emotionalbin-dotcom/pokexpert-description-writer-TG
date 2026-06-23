import re
content = open('inventory_decoded.txt', 'r', encoding='utf-8').read()
matches = re.finditer(r'1:\s*"([^"]*pose[^"]*)"', content, re.IGNORECASE)
poses = set([m.group(1) for m in matches])
print('Poses found:', len(poses))
for p in poses: print(p)
