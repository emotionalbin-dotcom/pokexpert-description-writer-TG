import re

with open('parse_final_locked.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken pokedex_matches line and the backslashes inside the regex block!
# Because the string was broken, let's just replace the whole chunk.
start_idx = content.find('pokedex_matches = re.findall')
end_idx = content.find('item_matches = re.findall(')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

# Now re-insert the logic properly!
pokedex_logic = r'''pokedex_matches = re.findall(r'  3 \{\n    .*?    3 \{\n(.*?)    \}\n  \}', full_content, re.DOTALL)
pokedex_unique = 0
pokedex_shiny = 0
for match in pokedex_matches:
    lines_match = match.strip().split('\n')
    if not lines_match: continue
    first_line = lines_match[0].strip()
    if first_line.startswith('3 {'):
        if '1:' in match:
            pokedex_unique += 1
            if re.search(r'^\s*(9|13):\s*[1-9]', match, re.MULTILINE):
                pokedex_shiny += 1
'''

content = content.replace('item_matches = re.findall(', pokedex_logic + '\nitem_matches = re.findall(')

with open('parse_final_locked.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed parse_final_locked.py!")
