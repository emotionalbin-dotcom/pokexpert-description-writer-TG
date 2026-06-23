import os

files_to_patch = ['parse_final_locked.py', 'parse_final_unlocked.py']

OLD = """pokedex_matches = re.findall(r'  3 \\{\\n    .*?    3 \\{\\n(.*?)    \\}\\n  \\}', full_content, re.DOTALL)
pokedex_unique = 0
pokedex_shiny = 0
for match in pokedex_matches:
    lines_match = match.strip().split('\\n')
    if not lines_match: continue
    first_line = lines_match[0].strip()
    if '1:' in match:
        pokedex_unique += 1
        if re.search(r'^\\s*(9|13):\\s*[1-9]', match, re.MULTILINE):
            pokedex_shiny += 1"""

NEW = """# --- POKEDEX: Read from pokedex_data.json written by JS interceptor ---
pokedex_unique = 0
pokedex_shiny = 0
if os.path.exists('pokedex_data.json'):
    try:
        with open('pokedex_data.json', 'r', encoding='utf-8') as _pf:
            _pd = json.load(_pf)
        pokedex_unique = _pd.get('unique_caught', 0)
        pokedex_shiny = _pd.get('shiny_species', 0)
    except Exception as _e:
        print(f'[WARN] Could not read pokedex_data.json: {_e}')
else:
    # Fallback: count field-10 blocks directly in decoded text (robust to \\r\\n)
    _poke_matches = re.findall(r'10\\s*\\{[\\s\\S]*?\\}', full_content)
    for _m in _poke_matches:
        if '1:' in _m:
            pokedex_unique += 1
# --- END POKEDEX ---"""

for filename in files_to_patch:
    if not os.path.exists(filename):
        print(f'SKIP: {filename} not found')
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Patched: {filename}')
    else:
        print(f'[WARN] Pattern not found in {filename} - trying partial match...')
        # Show the actual text around that section
        idx = content.find('pokedex_matches = re.findall')
        if idx != -1:
            print(repr(content[idx:idx+400]))
        else:
            print('pokedex_matches line not found at all!')
