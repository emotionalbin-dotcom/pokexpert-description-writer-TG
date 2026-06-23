import re

files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Pokedex logic
        start_idx = content.find('pokedex_matches = re.findall')
        end_idx = content.find('item_matches = re.findall(')

        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + content[end_idx:]

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

        # 2. TM definitions
        if 'fast_tms = items.get("1201"' not in content:
            content = content.replace('elite_charge_tm = items.get("1204", 0)', 'elite_charge_tm = items.get("1204", 0)\nfast_tms = items.get("1201", 0)\ncharged_tms = items.get("1202", 0)')

        # 3. to_bold
        bold_func = '''
def to_bold(text):
    bold_map = str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵")
    return str(text).translate(bold_map)

'''
        if 'def to_bold(text):' not in content:
            content = content.replace('# Generate the formatted text', bold_func + '# Generate the formatted text')

        # 4. Replacements
        old_block = '''lines.append("📖 𝟴𝟰𝟲 𝗨𝗻𝗶𝗾𝘂𝗲 𝗣𝗼𝗸𝗲𝗺𝗼𝗻 𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱")
lines.append("✨ 𝟲𝟮𝟱 𝗦𝗵𝗶𝗻𝘆 𝗦𝗽𝗲𝗰𝗶𝗲𝘀 𝗨𝗻𝗹𝗼𝗰𝗸𝗲𝗱")
lines.append("")
lines.append("🎒 𝗩𝗮𝗹𝘂𝗮𝗯𝗹𝗲 𝗜𝘁𝗲𝗺𝘀:")
lines.append("1,296 Rare Candies, 280 Rare XL Candies, 4 Master Balls, 51 Fast TMs, 73 Charged TMs, 39 Lucky Eggs, 71 Star Pieces, 34 Incense, 3 Super Incubators.")'''

        new_block = '''lines.append(f"📖 {to_bold(pokedex_unique)} 𝗨𝗻𝗶𝗾𝘂𝗲 𝗣𝗼𝗸𝗲𝗺𝗼𝗻 𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱")
lines.append(f"✨ {to_bold(pokedex_shiny)} 𝗦𝗵𝗶𝗻𝘆 𝗦𝗽𝗲𝗰𝗶𝗲𝘀 𝗨𝗻𝗹𝗼𝗰𝗸𝗲𝗱")
lines.append("")
lines.append("🎒 𝗩𝗮𝗹𝘂𝗮𝗯𝗹𝗲 𝗜𝘁𝗲𝗺𝘀:")

item_str = []
if rare_candy > 0: item_str.append(f"{rare_candy:,} Rare Candies")
if xl_rare_candy > 0: item_str.append(f"{xl_rare_candy:,} Rare XL Candies")
if master_balls > 0: item_str.append(f"{master_balls:,} Master Balls")
if fast_tms > 0: item_str.append(f"{fast_tms:,} Fast TMs")
if charged_tms > 0: item_str.append(f"{charged_tms:,} Charged TMs")
if lucky_eggs > 0: item_str.append(f"{lucky_eggs:,} Lucky Eggs")
if star_pieces > 0: item_str.append(f"{star_pieces:,} Star Pieces")
if incense > 0: item_str.append(f"{incense:,} Incense")
if super_incubators > 0: item_str.append(f"{super_incubators:,} Super Incubators")
if incubators > 0: item_str.append(f"{incubators:,} Incubators")
if not item_str: item_str.append("None")

lines.append(", ".join(item_str) + ".")'''

        content = content.replace(old_block, new_block)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
