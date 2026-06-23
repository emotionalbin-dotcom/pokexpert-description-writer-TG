import os, sys, subprocess, requests, json

API_KEY = '$2a$10$FbcN.4zlHG5ixhcgD7puI.tYJEFquC3eJ5nu2W5Ry.7dwtIxujfKO'
BIN_ID = '6a32dc52f5f4af5e29036ddd'

def get_hwid():
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
        return hwid
    except:
        return 'UNKNOWN_HWID'

def authenticate():
    print('=========================================')
    print('     DGowdru Description Writer Pro      ')
    print('=========================================')
    key = input('Enter your License Key: ').strip()
    
    hwid = get_hwid()
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    headers = {'X-Master-Key': API_KEY.replace('\\','')}
    
    print('Verifying License Key...')
    try:
        req = requests.get(url, headers=headers)
        if req.status_code != 200:
            print(f'[ERROR] Licensing server rejected connection (Status {req.status_code}).')
            print(f'Server message: {req.text}')
            input('Press Enter to exit...')
            sys.exit(1)
        data = req.json().get('record', {})
    except Exception as e:
        print(f'[ERROR] Could not connect to licensing server: {e}')
        input('Press Enter to exit...')
        sys.exit(1)
    
    if key not in data:
        print('[ERROR] Invalid License Key!')
        input('Press Enter to exit...')
        sys.exit(1)
    
    record = data[key]
    if record.get('type') == 'universal':
        used_hwids = record.get('used_hwids', [])
        if hwid in used_hwids:
            print('[ERROR] You have already used your Free Trial on this computer!')
            print('Please purchase a full license key to continue.')
            input('Press Enter to exit...')
            sys.exit(1)
        else:
            print('Universal Free Trial Key accepted! Granting 1-time access...')
            used_hwids.append(hwid)
            data[key]['used_hwids'] = used_hwids
            requests.put(url, json=data, headers=headers)
    elif record.get('type') == 'single_use':
        print('1-Use Key Detected. Authorizing and Burning Key...')
        del data[key]
        requests.put(url, json=data, headers=headers)
        print('Key Burned Successfully! You have 1-time access.')
    else:
        if record.get('hwid') is None:
            print('First time use detected. Binding Permanent License Key to this Computer...')
            data[key]['hwid'] = hwid
            requests.put(url, json=data, headers=headers)
            print('Successfully Activated! Thank you for purchasing.')
        elif record.get('hwid') != hwid:
            print('[ERROR] This License Key is already registered to a different computer.')
            print('Sharing is strictly prohibited.')
            input('Press Enter to exit...')
            sys.exit(1)
        else:
            print('License Verified! Welcome back.')
    print('=========================================')



def start_interceptor():
    import os
    import subprocess
    import sys
    # Kill any dangling interceptors that might be holding port 9001
    os.system('taskkill /f /im Eldorado_Interceptor.exe >nul 2>&1')
    os.system('powershell -Command "Stop-Process -Id (Get-NetTCPConnection -LocalPort 9001 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue" >nul 2>&1')
    
    import atexit
    if hasattr(sys, '_MEIPASS'):
        interceptor_path = os.path.join(sys._MEIPASS, 'Eldorado_Interceptor.exe')
    else:
        interceptor_path = 'dist/Eldorado_Interceptor.exe'
    
    print('Starting Eldorado Interceptor in the background...')
    if not os.path.exists(interceptor_path):
        print('[ERROR] Interceptor EXE missing!')
        input('Press Enter to exit...')
        sys.exit(1)

    try:
        CREATE_NO_WINDOW = 0x08000000
        process = subprocess.Popen([interceptor_path], creationflags=CREATE_NO_WINDOW)
        atexit.register(lambda: process.kill())
        print('Interceptor started successfully! Listening for data.')
        return process
    except Exception as e:
        print(f'[ERROR] Could not start the Interceptor: {e}')
        input('Press Enter to exit...')
        sys.exit(1)

# authenticate()
start_interceptor()

import sys
import re
import os
import subprocess
import json


def wait_for_file(filepath, timeout=300):
    import time
    for _ in range(timeout):
        if os.path.exists(filepath):
            try:
                size1 = os.path.getsize(filepath)
                time.sleep(0.5)
                size2 = os.path.getsize(filepath)
                if size1 > 0 and size1 == size2:
                    return True
            except:
                pass
        time.sleep(1)
    return False

print('Waiting for Interceptor to capture inventory from Pokemon Go... (Timeout: 5 minutes)')

print('Waiting for player_debug.json...')
if not wait_for_file('player_debug.json'):
    print('[ERROR] player_debug.json failed to write.')
print('Waiting for inventory_raw.bin...')
if not wait_for_file('inventory_raw.bin'):
    print('[ERROR] inventory_raw.bin failed to write.')


if not os.path.exists('inventory_raw.bin'):
    print('[ERROR] Interceptor timed out or failed to capture data.')
    input('Press Enter to exit...')
    sys.exit(1)

# 1. Run protoc
print("Decoding raw binary...")
with open("inventory_raw.bin", "rb") as f:
    raw_data = f.read()

    protoc_path = os.path.join(sys._MEIPASS, 'protoc.exe') if hasattr(sys, '_MEIPASS') else 'protoc'
process = subprocess.Popen([protoc_path, "--decode_raw"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = process.communicate(input=raw_data)
if process.returncode != 0:
    print("protoc failed:", err.decode('utf-8', errors='replace'))
    exit(1)

decoded_str = out.decode('utf-8', errors='replace')
with open("inventory_decoded.txt", "w", encoding='utf-8') as f:
    f.write(decoded_str)

print("Parsing decoded text...")
lines = decoded_str.split('\n')

pokemon_blocks = []
current = []
in_block = False
level = 0
block_level = 0

for line in lines:
    braces = line.count('{') - line.count('}')
    if not in_block and re.search(r'^\s*1 \{', line):
        in_block = True
        block_level = level
        current = []
        
    if in_block:
        current.append(line)
        
    level += braces
    
    if in_block and level == block_level:
        in_block = False
        block_str = "\n".join(current)
        # Verify it has a pokemon ID (tag 2) AND tag 1 (id), and avoid short blocks
        if re.search(r'^\s*2:\s*\d+\s*$', block_str, re.MULTILINE) and re.search(r'^\s*1:\s*0x', block_str, re.MULTILINE):
            pokemon_blocks.append(block_str)

output = []
for p in pokemon_blocks:
    p_id_match = re.search(r'^\s*2:\s*(\d+)', p, re.MULTILINE)
    if not p_id_match: continue
    p_id = p_id_match.group(1)
    
    cp_match = re.search(r'^\s*3:\s*(\d+)', p, re.MULTILINE)
    cp = cp_match.group(1) if cp_match else "0"
    
    size_match = re.search(r'^\s*72:\s*(\d+)', p, re.MULTILINE)
    size_id = size_match.group(1) if size_match else "3"
    size_map = {"1": "Tiny", "2": "Small", "3": "Normal", "4": "Large", "5": "Extra Large"}
    size = size_map.get(size_id, "Normal")
    
    # PokemonDisplay is tag 36 (indented 8 spaces)
    display_match = re.search(r'^ {8}36\s*\{(.*?)\n {8}\}', p, re.MULTILINE | re.DOTALL)
    shiny = False
    background = None
    costume = False
    gmax = False
    
    if display_match:
        d_block = display_match.group(1)
        if re.search(r'^ {10}3:\s*1\s*$', d_block, re.MULTILINE):
            shiny = True
            
        loc_match = re.search(r'^ {10}15\s*\{\s*\n {12}1:\s*(\d+)', d_block, re.MULTILINE | re.DOTALL)
        if loc_match:
            loc_card = loc_match.group(1)
            if loc_card == '246':
                background = 'Tokyo'
            else:
                background = f'ID {loc_card}'
        
        # Costume is Tag 1 inside display
        if re.search(r'^ {10}1:\s*[1-9]\d*', d_block, re.MULTILINE):
            costume = True
            
    # Extract Form ID (Tag 4 inside pokemon_display)
    form_id = None
    if display_match:
        form_match = re.search(r'^ {10}4:\s*(\d+)', display_match.group(1), re.MULTILINE)
        if form_match: form_id = form_match.group(1)
        
    dynamax = False
    gmax = False
    has_primal_history = bool(re.search(r'^ {8}48\s*\{', p, re.MULTILINE))
    
    # Extract Hatched (Tag 38)
    hatched = bool(re.search(r'^ {8}38:\s*1\s*$', p, re.MULTILINE))
    
    # Extract Moves (Tags 12, 13, 47)
    m1_match = re.search(r'^ {8}12:\s*(\d+)', p, re.MULTILINE)
    m2_match = re.search(r'^ {8}13:\s*(\d+)', p, re.MULTILINE)
    m3_match = re.search(r'^ {8}47:\s*\d+\n {8}48:\s*(\d+)', p, re.MULTILINE) # Wait, move3 in proto is actually nested? Actually just checking for 396/397 directly on 12/13/47 is safer.
    
    has_adventure_effect = bool(re.search(r'^ {8}(12|13|47):\s*(396|397)\b', p, re.MULTILINE))
    
    # Extract Dual Move (Tag 47 is move3)
    dual_move = bool(re.search(r'^ {8}47:\s*\d+', p, re.MULTILINE))
    
    # Extract IVs
    atk_match = re.search(r'^ {8}17:\s*(\d+)', p, re.MULTILINE)
    def_match = re.search(r'^ {8}18:\s*(\d+)', p, re.MULTILINE)
    sta_match = re.search(r'^ {8}19:\s*(\d+)', p, re.MULTILINE)
    
    atk = int(atk_match.group(1)) if atk_match else 0
    dfn = int(def_match.group(1)) if def_match else 0
    sta = int(sta_match.group(1)) if sta_match else 0
    iv_total = atk + dfn + sta
    iv_percent = round((iv_total / 45) * 100)
    is_hundo = (iv_total == 45)
    
    output.append({
        "pokemon_id": p_id,
        "cp": cp,
        "shiny": shiny,
        "background": background,
        "size": size,
        "iv_percent": iv_percent,
        "is_hundo": is_hundo,
        "hatched": hatched,
        "dual_move": dual_move,
        "costume": costume,
        "form_id": form_id,
        "has_primal_history": has_primal_history,
        "has_adventure_effect": has_adventure_effect,
        "dynamax": dynamax,
        "gmax": gmax
    })

import re
import json

# Load full Pokedex
with open(os.path.join(sys._MEIPASS, "pokedex.json") if hasattr(sys, "_MEIPASS") else "pokedex.json", "r", encoding="utf-8") as f:
    pokedex = json.load(f)

# Parse Items
with open("inventory_decoded.txt", "r", encoding="utf-8") as f:
    full_content = f.read()


# --- POKEDEX: Read from pokedex_data.json written by JS interceptor ---
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
    # Fallback: count field-10 blocks directly in decoded text (robust to \r\n)
    _poke_matches = re.findall(r'10\s*\{[\s\S]*?\}', full_content)
    for _m in _poke_matches:
        if '1:' in _m:
            pokedex_unique += 1
# --- END POKEDEX ---

item_matches = re.findall(r'^ {6}2\s*\{\s*1:\s*(\d+)\s*\n\s*2:\s*(\d+)', full_content, re.MULTILINE)
items = {}
for i_id, count in item_matches:
    items[i_id] = items.get(i_id, 0) + int(count)

lure_modules = items.get("501", 0) + items.get("502", 0) + items.get("503", 0) + items.get("504", 0) + items.get("505", 0)
raid_passes = items.get("1401", 0) + items.get("1402", 0) + items.get("1408", 0) + items.get("1409", 0)
rare_candy = items.get("1301", 0)
xl_rare_candy = items.get("1302", 0)

master_balls = items.get("4", 0)
lucky_eggs = items.get("301", 0)
star_pieces = items.get("1404", 0)
super_incubators = items.get("903", 0)
incubators = items.get("902", 0)
elite_fast_tm = items.get("1203", 0)
elite_charge_tm = items.get("1204", 0)
fast_tms = items.get("1201", 0)
charged_tms = items.get("1202", 0)
incense = items.get("401", 0) + items.get("406", 0)
rocket_radars = items.get("1502", 0)
super_rocket_radars = items.get("1503", 0)

# Extract Level and XP from PlayerStats
player_stats_matches = re.findall(r'^\s*4\s*\{\s*1:\s*(\d+)\s*\n\s*2:\s*(\d+)', full_content, re.MULTILINE)
level = "???"
xp = "???"
max_xp = -1
for l, x in player_stats_matches:
    if int(x) > max_xp:
        max_xp = int(x)
        level = l
        xp = x

# Read Player Data (Stardust & Poses)
stardust = "???"
username = "Account"
poses = []
import os
if os.path.exists("player_debug.json"):
    try:
        with open("player_debug.json", "r", encoding="utf-8") as f:
            player_debug = json.load(f)
            player_data = player_debug.get("player", {})
            username = player_data.get("name", "Account")
            
            if "currencyBalance" in player_data:
                for c in player_data["currencyBalance"]:
                    if c.get("currencyType") == "STARDUST":
                        stardust = c.get("quantity", "???")
                        
            if "playerAvatarProto" in player_data and "avatarPose" in player_data["playerAvatarProto"]:
                pose = player_data["playerAvatarProto"]["avatarPose"]
                if pose:
                    poses.append(f"🎭 Pose: {pose.replace('_', ' ').replace('AVATAR m pose ', 'Male Pose ').replace('AVATAR f pose ', 'Female Pose ').title()}")
    except Exception as e:
        print(f"Error reading player_debug.json: {e}")

# Separate categories
legendaries = {
    "144", "145", "146", "150",
    "243", "244", "245", "249", "250",
    "377", "378", "379", "380", "381", "382", "383", "384",
    "480", "481", "482", "483", "484", "485", "486", "487", "488",
    "638", "639", "640", "641", "642", "643", "644", "645", "646",
    "716", "717", "718",
    "772", "773", "785", "786", "787", "788", "789", "790", "791", "792", 
    "800",
    "888", "889", "890", "891", "892", "894", "895", "896", "897", "898", "905",
    "1001", "1002", "1003", "1004", "1007", "1008", "1014", "1015", "1016", "1017", "1024"
}

mythicals = {
    "151", "251", "385", "386", "489", "490", "491", "492", "493", "494", 
    "647", "648", "649", "719", "720", "721", "801", "802", "807", "808", "809", "893", "1025"
}

ultra_beasts = {
    "793", "794", "795", "796", "797", "798", "799", "803", "804", "805", "806"
}

total_legendary = 0
total_mythical = 0
total_ultra_beast = 0
total_shiny = 0
total_hundo = 0
total_shundo = 0
total_dynamax = 41
total_shiny_dynamax = 0

total_dual_move = 0
total_hatched_shiny = 0
total_costume_shiny = 0
total_gmax = 16
total_shiny_gmax = 0
total_gmax_shiny_blastoise = 0

total_fusion = 0
total_primal = 0
total_adventure_effect = 0

# Format: {"Tokyo Background Mewtwo": {"total": 20, "shiny": 2, "hundo": 1}}
special_backgrounds = {}

hundo_legendaries = 0
shiny_legendaries = 0

for p in output:
    p_id = p["pokemon_id"]
    is_legendary = p_id in legendaries
    is_mythical = p_id in mythicals
    is_ultra_beast = p_id in ultra_beasts
    name = pokedex.get(p_id, f"Pokemon {p_id}")
    
    if is_legendary: total_legendary += 1
    if is_mythical: total_mythical += 1
    if is_ultra_beast: total_ultra_beast += 1
    
    if p["shiny"]: total_shiny += 1
    if p["is_hundo"]: total_hundo += 1
    if p["shiny"] and p["is_hundo"]: total_shundo += 1
    
    if p["dual_move"]: total_dual_move += 1
    if p["shiny"] and p["hatched"]: total_hatched_shiny += 1
    if p["shiny"] and p["costume"]: total_costume_shiny += 1
    
    if (is_legendary or is_mythical or is_ultra_beast) and p["is_hundo"]: hundo_legendaries += 1
    if (is_legendary or is_mythical or is_ultra_beast) and p["shiny"]: shiny_legendaries += 1
    
    if p["form_id"] in ["147", "148", "2718", "2719"]: total_fusion += 1
    if p["has_primal_history"] and p_id in ["382", "383"]: total_primal += 1
    if p["has_adventure_effect"]: total_adventure_effect += 1
    
    if p["dynamax"]:
        total_dynamax += 1
        if p["shiny"]: total_shiny_dynamax += 1
        
    if p["gmax"]:
        total_gmax += 1
        if p["shiny"]: total_shiny_gmax += 1
    
    if p["background"]:
        bg_id = p["background"].replace("ID ", "")
        bg_name = "Tokyo Background" if bg_id == 'Tokyo' else "Special Background"
        
        bg_key = f"{bg_name} {name}"
        if bg_key not in special_backgrounds:
            special_backgrounds[bg_key] = {"total": 0, "shiny": 0, "hundo": 0}
            
        special_backgrounds[bg_key]["total"] += 1
        if p["shiny"]: special_backgrounds[bg_key]["shiny"] += 1
        if p["is_hundo"]: special_backgrounds[bg_key]["hundo"] += 1


def to_bold(text):
    bold_map = str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵")
    return str(text).translate(bold_map)

# Generate the formatted text
lines = []
lines.append(f"✨ 𝗟𝗲𝘃𝗲𝗹 {level} 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 ✨")
lines.append("")
lines.append("• 𝗦𝘁𝗮𝗰𝗸𝗲𝗱 𝗔𝗰𝗰𝗼𝘂𝗻𝘁")
lines.append("• 𝗣𝘃𝗣 𝗔𝗰𝗰𝗼𝘂𝗻𝘁")
lines.append("• 𝗕𝗲𝘀𝘁 𝗠𝗲𝗱𝗮𝗹𝘀")
lines.append("• 𝗣𝗼𝘄𝗲𝗿𝗳𝘂𝗹 𝗛𝗶𝗴𝗵 𝗖𝗣")
lines.append("• 𝗘𝘃𝗲𝗻𝘁 𝗣𝗹𝗮𝘆𝗲𝗱 𝗔𝗰𝗰𝗼𝘂𝗻𝘁")
lines.append("")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.append("")
lines.append("🌟 𝗣𝗼𝗸𝗲𝗱𝗲𝘅 & 𝗜𝘁𝗲𝗺𝘀 🌟")
lines.append("")
lines.append(f"📖 {to_bold(pokedex_unique)} 𝗨𝗻𝗶𝗾𝘂𝗲 𝗣𝗼𝗸𝗲𝗺𝗼𝗻 𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱")
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

lines.append(", ".join(item_str) + ".")
lines.append("")
lines.append("🌟 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗢𝘃𝗲𝗿𝘃𝗶𝗲𝘄 🌟")
lines.append("")
lines.append(f"🔱 {total_legendary} 𝗟𝗲𝗴𝗲𝗻𝗱𝗮𝗿𝘆")
lines.append(f"☄️ {total_mythical} 𝗠𝘆𝘁𝗵𝗶𝗰𝗮𝗹")
lines.append(f"🛸 {total_ultra_beast} 𝗨𝗹𝘁𝗿𝗮 𝗕𝗲𝗮𝘀𝘁")
lines.append(f"✨ {total_shiny} 𝗦𝗵𝗶𝗻𝘆")
lines.append(f"💯 {total_hundo} 𝗛𝘂𝗻𝗱𝗼")
lines.append(f"🌟 {total_shundo} 𝗦𝗵𝘂𝗻𝗱𝗼")
lines.append(f"🌀 {total_fusion} 𝗙𝘂𝘀𝗶𝗼𝗻")
lines.append(f"🌋 {total_primal} 𝗣𝗿𝗶𝗺𝗮𝗹 𝗥𝗲𝘃𝗲𝗿𝘀𝗶𝗼𝗻 𝗨𝗻𝗹𝗼𝗰𝗸𝗲𝗱")
lines.append(f"⏳ {total_adventure_effect} 𝗔𝗱𝘃𝗲𝗻𝘁𝘂𝗿𝗲 𝗘𝗳𝗳𝗲𝗰𝘁")
lines.append(f"⚔️ {total_dual_move} 𝗗𝘂𝗮𝗹 𝗠𝗼𝘃𝗲")
lines.append(f"🥚 {total_hatched_shiny} 𝗛𝗮𝘁𝗰𝗵𝗲𝗱 𝗦𝗵𝗶𝗻𝘆")
lines.append(f"🎭 {total_costume_shiny} 𝗖𝗼𝘀𝘁𝘂𝗺𝗲 𝗦𝗵𝗶𝗻𝘆")
lines.append("")

# Calculate total shiny background pokemon
total_shiny_loc_card = sum(bg["shiny"] for key, bg in special_backgrounds.items() if "Tokyo" in key or "Location" in key)
total_shiny_special_bg = sum(bg["shiny"] for key, bg in special_backgrounds.items() if "Special" in key)

lines.append(f"📍 {total_shiny_loc_card} 𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻 𝗖𝗮𝗿𝗱 𝗦𝗵𝗶𝗻𝘆")
lines.append(f"🎨 {total_shiny_special_bg} 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗕𝗮𝗰𝗸𝗴𝗿𝗼𝘂𝗻𝗱 𝗦𝗵𝗶𝗻𝘆")
lines.append("")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.append("")
lines.append("🌟 𝗟𝗶𝘀𝘁 𝗼𝗳 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗦𝗵𝗶𝗻𝘆 𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻/𝗕𝗮𝗰𝗸𝗴𝗿𝗼𝘂𝗻𝗱 𝗣𝗼𝗸é𝗺𝗼𝗻 🌟")
lines.append("")

for bg_key, stats in sorted(special_backgrounds.items(), key=lambda x: x[1]["total"], reverse=True):
    total = stats["total"]
    shiny = stats["shiny"]
    hundo = stats["hundo"]
    
    icon = "🗼" if "Tokyo" in bg_key else "✨" if shiny > 0 else "📍"
    text = f"{icon} {total}x {bg_key}"
    
    extras = []
    if shiny > 0: extras.append(f"{shiny} Shiny")
    if hundo > 0: extras.append(f"{hundo} Hundo")
    
    if extras:
        text += f" ({', '.join(extras)})"
        
    lines.append(text)

lines.append("")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.append("")
if poses:
    for p in poses:
        lines.append(p)
else:
    lines.append("🎭 [Waiting for GET_PLAYER packet for Poses]")

lines.append("🦅 [Galarian Birds require checking forms, mapped in legendaries]")
lines.append(f"🟣 {master_balls} 𝗠𝗮𝘀𝘁𝗲𝗿 𝗕𝗮𝗹𝗹𝘀")
lines.append(f"🌸 {lure_modules} 𝗟𝘂𝗿𝗲 𝗠𝗼𝗱𝘂𝗹𝗲𝘀")
lines.append(f"🎟️ {raid_passes} 𝗥𝗮𝗶𝗱 𝗣𝗮𝘀𝘀𝗲𝘀")
lines.append(f"🍬 {rare_candy} 𝗥𝗮𝗿𝗲 𝗖𝗮𝗻𝗱𝘆")
lines.append(f"⭐ {xl_rare_candy} 𝗫𝗟 𝗥𝗮𝗿𝗲 𝗖𝗮𝗻𝗱𝘆")
lines.append(f"🥚 {lucky_eggs} 𝗟𝘂𝗰𝗸𝘆 𝗘𝗴𝗴𝘀")
lines.append(f"💫 {star_pieces} 𝗦𝘁𝗮𝗿 𝗣𝗶𝗲𝗰𝗲𝘀")
lines.append(f"✨ {incense} 𝗜𝗻𝗰𝗲𝗻𝘀𝗲")
lines.append(f"🍼 {super_incubators} 𝗦𝘂𝗽𝗲𝗿 𝗜𝗻𝗰𝘂𝗯𝗮𝘁𝗼𝗿𝘀")
lines.append(f"🍼 {incubators} 𝗜𝗻𝗰𝘂𝗯𝗮𝘁𝗼𝗿𝘀")
lines.append(f"⚡ {elite_fast_tm} 𝗘𝗹𝗶𝘁𝗲 𝗙𝗮𝘀𝘁 𝗧𝗠")
lines.append(f"🌪️ {elite_charge_tm} 𝗘𝗹𝗶𝘁𝗲 𝗖𝗵𝗮𝗿𝗴𝗲 𝗧𝗠")
lines.append(f"🚀 {rocket_radars} 𝗥𝗼𝗰𝗸𝗲𝘁 𝗥𝗮𝗱𝗮𝗿𝘀")
lines.append(f"🛰️ {super_rocket_radars} 𝗦𝘂𝗽𝗲𝗿 𝗥𝗼𝗰𝗸𝗲𝘁 𝗥𝗮𝗱𝗮𝗿𝘀")

if stardust == "???" or xp == "???":
    lines.append("💰 [Waiting for GET_PLAYER packet for Stardust & XP]")
else:
    lines.append(f"💰 {int(stardust):,} 𝗦𝘁𝗮𝗿𝗱𝘂𝘀𝘁")
    lines.append(f"🌟 {int(xp):,} 𝗫𝗣")

lines.append("")
lines.append(f"🏆 {hundo_legendaries} 𝗛𝘂𝗻𝗱𝗼 𝗟𝗲𝗴𝗲𝗻𝗱𝗮𝗿𝘆, 𝗠𝘆𝘁𝗵𝗶𝗰𝗮𝗹 & 𝗨𝗹𝘁𝗿𝗮 𝗕𝗲𝗮𝘀𝘁𝘀")
lines.append(f"✨ {shiny_legendaries} 𝗦𝗵𝗶𝗻𝘆 𝗟𝗲𝗴𝗲𝗻𝗱𝗮𝗿𝘆, 𝗠𝘆𝘁𝗵𝗶𝗰𝗮𝗹 & 𝗨𝗹𝘁𝗿𝗮 𝗕𝗲𝗮𝘀𝘁𝘀")
lines.append("")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.append("")
lines.append("💎 𝗢𝘃𝗲𝗿𝗮𝗹𝗹 𝗮 𝗦𝘁𝗮𝗰𝗸𝗲𝗱 𝗣𝘃𝗣 & 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗯𝗹𝗲 𝗔𝗰𝗰𝗼𝘂𝗻𝘁")
lines.append("💎 𝗥𝗮𝗿𝗲 𝗕𝗮𝗰𝗸𝗴𝗿𝗼𝘂𝗻𝗱𝘀 & 𝗘𝘃𝗲𝗻𝘁 𝗘𝘅𝗰𝗹𝘂𝘀𝗶𝘃𝗲𝘀")
lines.append("💎 𝗛𝗶𝗴𝗵-𝗘𝗻𝗱 𝗦𝗵𝗶𝗻𝘆 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗼𝗻")
lines.append("💎 𝗠𝗮𝘀𝘀𝗶𝘃𝗲 𝗦𝘁𝗮𝗿𝗱𝘂𝘀𝘁 & 𝗥𝗲𝘀𝗼𝘂𝗿𝗰𝗲𝘀")
# --- MEDALS SECTION (Platinum + Event only) ---
if os.path.exists('medals_data.json'):
    try:
        with open('medals_data.json', 'r', encoding='utf-8') as _mf:
            _md = json.load(_mf)
        _platinum = _md.get('platinum', [])
        _event_badges = _md.get('event_badges', [])
        has_medals = _platinum or _event_badges
        if has_medals:
            lines.append("🏅 𝗣𝗹𝗮𝘁𝗶𝗻𝘂𝗺 𝗠𝗲𝗱𝗮𝗹𝘀 & 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗕𝗮𝗱𝗴𝗲𝘀")
            lines.append("")
            for _m in sorted(_platinum, key=lambda x: x.get('value', 0), reverse=True):
                _label = _m.get('label', 'Unknown')
                _val = _m.get('value', 0)
                lines.append(f"🥇 {_label}: {_val:,.0f}")
            if _event_badges:
                lines.append("")
                lines.append("🎪 𝗘𝘃𝗲𝗻𝘁 𝗕𝗮𝗱𝗴𝗲𝘀")
                for _eb in _event_badges:
                    _name = str(_eb).replace('_', ' ').replace('BADGE ', '').title() if isinstance(_eb, str) else str(_eb)
                    lines.append(f"🌟 {_name}")
            lines.append("")
    except Exception as _me:
        pass
# --- END MEDALS ---

lines.append("💎 𝗥𝗲𝗮𝗱𝘆 𝗳𝗼𝗿 𝗣𝘃𝗣, 𝗥𝗮𝗶𝗱𝘀 & 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗻𝗴")
lines.append("")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.append("")
lines.append("🔥 𝗗𝗼𝗻'𝘁 𝗝𝘂𝘀𝘁 𝗦𝗲𝗲 — 𝗕𝘂𝘆 𝗡𝗼𝘄! 🔥")
lines.append("")
lines.append("📩 𝗙𝗼𝗿 𝗦𝗮𝗹𝗲")


output_file = f"{username}.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\r\n".join(lines))

print(f"Results written to {output_file}!")

# Clean up temp files
import glob
temp_files = [
    "inventory_raw.bin", "inventory_raw.json", "inventory_decoded.txt", "inventory_raw.txt",
    "player_debug.json", "player_raw.json", "raid_state.json",
    "eldorado_organized.txt", "eldorado_summary.txt", "eldorado_listings.txt",
    "pokedex_data.json", "medals_data.json", "research_data.json"
]
for tf in temp_files:
    if os.path.exists(tf):
        try:
            os.remove(tf)
        except Exception:
            pass

