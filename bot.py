import os
import sys
import json
import logging
import asyncio
import string
import random
import threading
from flask import Flask, request, jsonify
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask Setup
flask_app = Flask(__name__)
# Telegram Bot Application global reference
tg_application = None

# Admin configuration
ADMIN_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", 6040671411)) # Default to user ID if not configured
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8906742255:AAHZuJIAmVKvLD5c8nDNa1lPSGQKJcBIOcA")

API_KEY = '$2a$10$FbcN.4zlHG5ixhcgD7puI.tYJEFquC3eJ5nu2W5Ry.7dwtIxujfKO'
BIN_ID = '6a32dc52f5f4af5e29036ddd'

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

# jsonbin.io Database Helpers
def get_db():
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    headers = {'X-Master-Key': API_KEY.replace('\\', '')}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json().get('record', {})
        else:
            logger.error(f"Error fetching DB: {r.status_code} {r.text}")
            return {}
    except Exception as e:
        logger.error(f"Exception fetching DB: {e}")
        return {}

def save_db(data):
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    headers = {
        'X-Master-Key': API_KEY.replace('\\', ''),
        'Content-Type': 'application/json'
    }
    try:
        r = requests.put(url, json=data, headers=headers)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Exception saving DB: {e}")
        return False

def check_license(user_id):
    db = get_db()
    user_key = f"user_{user_id}"
    if user_key in db:
        user_profile = db[user_key]
        if user_profile.get("type") == "lifetime":
            return True, "lifetime", -1
        elif user_profile.get("type") == "single":
            uses = user_profile.get("uses_left", 0)
            if uses > 0:
                return True, "single", uses
            return False, "single", 0
    return False, "none", 0

def consume_use(user_id):
    db = get_db()
    user_key = f"user_{user_id}"
    if user_key in db:
        user_profile = db[user_key]
        if user_profile.get("type") == "lifetime":
            return True
        elif user_profile.get("type") == "single":
            uses = user_profile.get("uses_left", 0)
            if uses > 0:
                db[user_key]["uses_left"] = uses - 1
                save_db(db)
                return True
    return False

def generate_key(key_type):
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(12))
    if key_type == 'lifetime':
        return f'DGowdru-{suffix}'
    else:
        return f'DG1USE-{suffix}'

def add_key_to_db(key, key_type):
    db = get_db()
    if key_type == 'lifetime':
        db[key] = {'hwid': None, 'type': 'permanent'}
    else:
        db[key] = {'hwid': None, 'type': 'single_use'}
    save_db(db)

# Thread-safe Telegram Sending Helpers
def send_telegram_file(chat_id, filepath, caption=""):
    if tg_application is None:
        logger.error("Telegram application not initialized yet!")
        return False
    
    async def _send():
        with open(filepath, 'rb') as f:
            await tg_application.bot.send_document(
                chat_id=chat_id,
                document=f,
                caption=caption
            )
            
    future = asyncio.run_coroutine_threadsafe(_send(), tg_application.loop)
    try:
        future.result(timeout=30)
        return True
    except Exception as e:
        logger.error(f"Error sending telegram file: {e}")
        return False

def send_telegram_message(chat_id, text):
    if tg_application is None:
        logger.error("Telegram application not initialized yet!")
        return False
    
    async def _send():
        await tg_application.bot.send_message(
            chat_id=chat_id,
            text=text
        )
        
    future = asyncio.run_coroutine_threadsafe(_send(), tg_application.loop)
    try:
        future.result(timeout=30)
        return True
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")
        return False

# Description Generator Logic
def generate_user_description(user_id):
    user_dir = f"data/{user_id}"
    
    # 1. Load Pokedex mapping
    pokedex = {}
    pokedex_path = "pokedex.json"
    if os.path.exists(pokedex_path):
        try:
            with open(pokedex_path, "r", encoding="utf-8") as f:
                pokedex = json.load(f)
        except Exception as e:
            logger.error(f"Error loading pokedex: {e}")
            
    # 2. Load Pokedex unique stats
    pokedex_unique = 0
    pokedex_shiny = 0
    pokedex_data_path = f"{user_dir}/pokedex_data.json"
    if os.path.exists(pokedex_data_path):
        try:
            with open(pokedex_data_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
                pokedex_unique = p_data.get("unique_caught", 0)
                pokedex_shiny = p_data.get("shiny_species", 0)
        except Exception:
            pass
            
    # 3. Load Items
    items = {}
    items_path = f"{user_dir}/items_data.json"
    if os.path.exists(items_path):
        try:
            with open(items_path, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            pass
            
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
    
    # 4. Load Level and XP
    level = "???"
    xp = "???"
    level_xp_path = f"{user_dir}/level_xp.json"
    if os.path.exists(level_xp_path):
        try:
            with open(level_xp_path, "r", encoding="utf-8") as f:
                lx = json.load(f)
                level = lx.get("level", "???")
                xp = lx.get("xp", "???")
        except Exception:
            pass
            
    # 5. Load Player Data
    stardust = "???"
    username = "Account"
    poses = []
    player_debug_path = f"{user_dir}/player_debug.json"
    if os.path.exists(player_debug_path):
        try:
            with open(player_debug_path, "r", encoding="utf-8") as f:
                player_debug = json.load(f)
                player_data = player_debug.get("player", {})
                username = player_data.get("name", "Account")
                
                if "currency_balance" in player_data:
                    for c in player_data["currency_balance"]:
                        if str(c.get("currency_type", "")).upper() == "STARDUST":
                            stardust = c.get("quantity", "???")
                            
                if "player_avatar_proto" in player_data and "avatar_pose" in player_data["player_avatar_proto"]:
                    pose = player_data["player_avatar_proto"]["avatar_pose"]
                    if pose:
                        poses.append(f"🎭 Pose: {pose.replace('_', ' ').replace('AVATAR m pose ', 'Male Pose ').replace('AVATAR f pose ', 'Female Pose ').title()}")
        except Exception:
            pass

    # 6. Load Pokemon
    pokemon_list = []
    inventory_path = f"{user_dir}/inventory_raw.json"
    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, "r", encoding="utf-8") as f:
                pokemon_list = json.load(f)
        except Exception:
            pass

    total_legendary = 0
    total_mythical = 0
    total_ultra_beast = 0
    total_shiny = 0
    total_hundo = 0
    total_shundo = 0
    total_dynamax = 0
    total_shiny_dynamax = 0
    total_gmax = 0
    total_shiny_gmax = 0
    total_fusion = 0
    total_primal = 0
    total_adventure_effect = 0
    total_dual_move = 0
    total_hatched_shiny = 0
    total_costume_shiny = 0
    special_backgrounds = {}
    hundo_legendaries = 0
    shiny_legendaries = 0

    for p in pokemon_list:
        p_id = str(p.get("pokemon_id", ""))
        is_legendary = p_id in legendaries
        is_mythical = p_id in mythicals
        is_ultra_beast = p_id in ultra_beasts
        name = pokedex.get(p_id, f"Pokemon {p_id}")
        
        display = p.get("pokemon_display", {})
        shiny = display.get("shiny", False)
        
        atk = p.get("individual_attack", 0)
        dfn = p.get("individual_defense", 0)
        sta = p.get("individual_stamina", 0)
        is_hundo = (atk == 15 and dfn == 15 and sta == 15)
        
        move1 = p.get("move_1") or p.get("move1")
        move2 = p.get("move_2") or p.get("move2")
        move3 = p.get("move_3") or p.get("move3") or p.get("move3_proto") or p.get("move_3_proto")
        
        dual_move = move3 is not None and move3 != 0
        
        # Hatched check
        hatched = p.get("hatched") or p.get("is_hatched") or (p.get("is_egg") == False and p.get("pokeball") == 0)
        hatched = bool(hatched)
        
        costume = display.get("costume", 0) > 0
        
        form_str = str(display.get("form", "")).upper()
        dynamax = "DYNAMAX" in form_str
        gmax = "GIGANTAMAX" in form_str
        
        # Adventure effect
        has_adventure_effect = any(m in [396, 397, '396', '397'] for m in [move1, move2, move3] if m is not None)
        
        # Fusion check
        form_id = str(display.get("form", ""))
        is_fusion = form_id in ["147", "148", "2718", "2719"] or "DUSK_MANE" in form_str or "DAWN_WINGS" in form_str
        
        # Primal check
        has_primal_history = p.get("has_primal_history") or p.get("primal_reversion") is not None
        is_primal = has_primal_history and p_id in ["382", "383", 382, 383, "KYOGRE", "GROUDON"]

        if is_legendary: total_legendary += 1
        if is_mythical: total_mythical += 1
        if is_ultra_beast: total_ultra_beast += 1
        
        if shiny: total_shiny += 1
        if is_hundo: total_hundo += 1
        if shiny and is_hundo: total_shundo += 1
        
        if dual_move: total_dual_move += 1
        if shiny and hatched: total_hatched_shiny += 1
        if shiny and costume: total_costume_shiny += 1
        
        if (is_legendary or is_mythical or is_ultra_beast) and is_hundo: hundo_legendaries += 1
        if (is_legendary or is_mythical or is_ultra_beast) and shiny: shiny_legendaries += 1
        
        if is_fusion: total_fusion += 1
        if is_primal: total_primal += 1
        if has_adventure_effect: total_adventure_effect += 1
        
        if dynamax:
            total_dynamax += 1
            if shiny: total_shiny_dynamax += 1
        if gmax:
            total_gmax += 1
            if shiny: total_shiny_gmax += 1

        # Background cards
        location_card = display.get("location_card", {}).get("location_card")
        origin_events = p.get("origin_events", [])
        background = None
        if location_card:
            loc_id = str(location_card)
            if loc_id == '246' or 'TOKYO' in loc_id.upper():
                background = 'Tokyo'
            else:
                background = f'ID {loc_id}'
        elif origin_events and len(origin_events) > 0:
            background = str(origin_events[0])

        if background:
            bg_name = "Tokyo Background" if background == 'Tokyo' else "Special Background"
            bg_key = f"{bg_name} {name}"
            if bg_key not in special_backgrounds:
                special_backgrounds[bg_key] = {"total": 0, "shiny": 0, "hundo": 0}
            special_backgrounds[bg_key]["total"] += 1
            if shiny: special_backgrounds[bg_key]["shiny"] += 1
            if is_hundo: special_backgrounds[bg_key]["hundo"] += 1

    def to_bold(text):
        bold_map = str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵")
        return str(text).translate(bold_map)

    # Output lines assembly
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
    lines.append(f"🥚 {lucky_eggs} 𝗟𝘂𝗰ky 𝗘𝗴𝗴𝘀")
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
        try:
            lines.append(f"💰 {int(stardust):,} 𝗦𝘁𝗮𝗿𝗱𝘂𝘀𝘁")
            lines.append(f"🌟 {int(xp):,} 𝗫𝗣")
        except Exception:
            lines.append(f"💰 {stardust} 𝗦𝘁𝗮𝗿𝗱𝘂𝘀𝘁")
            lines.append(f"🌟 {xp} 𝗫𝗣")
            
    lines.append("")
    lines.append(f"🏆 {hundo_legendaries} 𝗙𝗹𝗻𝗱𝗼 𝗙𝗲𝗴𝗲𝗻𝗱𝗮𝗿𝘆, 𝗠𝘆𝘁𝗵𝗶𝗰𝗮𝗹 & 𝗨𝗹𝘁𝗿𝗮 𝗕𝗲𝗮𝘀𝘁𝘀")
    lines.append(f"✨ {shiny_legendaries} 𝗦𝗵𝗶𝗻𝘆 𝗙𝗲𝗴𝗲𝗻𝗱𝗮𝗿𝘆, 𝗠𝘆𝘁𝗵𝗶𝗰𝗮𝗹 & 𝗨𝗹𝘁𝗿𝗮 𝗕𝗲𝗮𝘀𝘁𝘀")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("")
    
    # 8. Special Research
    research_path = f"{user_dir}/research_data.json"
    if os.path.exists(research_path):
        try:
            with open(research_path, 'r', encoding='utf-8') as f:
                rd = json.load(f)
            special = rd.get('special_research', [])
            if special:
                lines.append("🔬 𝗦𝗳𝗲𝗰𝗶𝗮𝗹 𝗥𝗲𝘀𝗲𝗮𝗿𝗰𝗵 𝗤𝗹𝗲𝘀𝘁𝘀")
                lines.append("")
                for q in special:
                    title = q.get('title', 'Unknown')
                    status = q.get('status', '')
                    icon = "✅" if 'COMPLETE' in str(status).upper() else "🟡" if q.get('completed_steps', 0) > 0 else "🔴"
                    lines.append(f"{icon} {title}")
                lines.append("")
        except Exception:
            pass
            
    # 9. Medals (Platinum + Event only)
    medals_path = f"{user_dir}/medals_data.json"
    if os.path.exists(medals_path):
        try:
            with open(medals_path, 'r', encoding='utf-8') as f:
                md = json.load(f)
            platinum = md.get('platinum', [])
            event_badges = md.get('event_badges', [])
            if platinum or event_badges:
                lines.append("🏅 𝗣𝗹𝗮𝘁𝗶𝗻𝘂𝗺 𝗠𝗲𝗱𝗮𝗹𝘀 & 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗕𝗮𝗱𝗴𝗲𝘀")
                lines.append("")
                for m in sorted(platinum, key=lambda x: x.get('value', 0), reverse=True):
                    label = m.get('label', 'Unknown')
                    val = m.get('value', 0)
                    lines.append(f"🥇 {label}: {val:,.0f}")
                if event_badges:
                    lines.append("")
                    lines.append("🎪 𝗘𝘃𝗲𝗻𝘁 𝗕𝗮𝗱𝗴𝗲𝘀")
                    for eb in event_badges:
                        name = str(eb).replace('_', ' ').replace('BADGE ', '').title() if isinstance(eb, str) else str(eb)
                        lines.append(f"🌟 {name}")
                lines.append("")
        except Exception:
            pass
            
    lines.append("💲 𝗢𝘃𝗲𝗿𝗮𝗹𝗹 𝗮 𝗦𝘁𝗮𝗰𝗸𝗲𝗱 𝗣𝘃𝗣 & 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗯𝗹𝗲 𝗔𝗰𝗰𝗼𝘂𝗻𝘁")
    lines.append("💎 𝗥𝗮𝗿𝗲 𝗕𝗮𝗰𝗸𝗴𝗿𝗼𝘂𝗻𝗱𝘀 & 𝗘𝘃𝗲𝗻𝘁 𝗘𝘅𝗰𝗹𝘂𝘀𝗶𝘃𝗲𝘀")
    lines.append("💎 𝗛𝗶𝗴𝗵-𝗘𝗻𝗱 𝗦𝗵𝗶𝗻𝘆 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗼𝗻")
    lines.append("💎 𝗠𝗮𝘀𝘀𝗶𝘃𝗲 𝗦𝘁𝗮𝗿𝗱𝘂𝘀𝘁 & 𝗥𝗲𝘀𝗼𝘂𝗿𝗰𝗲𝘀")
    lines.append("💎 𝗥𝗲𝗮𝗱𝘆 𝗳𝗼𝗿 𝗣𝘃𝗣, 𝗥𝗮𝗶𝗱𝘀 & 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗻𝗴")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("🔥 𝗗𝗼𝗻'𝘁 𝗝𝘂𝘀𝘁 𝗦𝗲𝗲 — 𝗕𝘂𝘆 𝗡𝗼𝘄! 🔥")
    lines.append("")
    lines.append("📩 𝗙𝗼𝗿 𝗦𝗮𝗹𝗲")
    
    # Write to final file
    output_file = f"{user_dir}/{username}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))
        
    return username, output_file

# Flask Route for triggering description generation
@flask_app.route('/internal/trigger_generate', methods=['POST'])
def trigger_generate():
    data = request.json or {}
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing userId"}), 400
        
    logger.info(f"[Internal] Received generate trigger for user: {user_id}")
    
    # 1. Check license status
    licensed, ltype, uses = check_license(user_id)
    if not licensed:
        send_telegram_message(
            chat_id=int(user_id),
            text="❌ Your Polygon sent account data, but you do not have an active license.\n\nType /status to check your balance or /redeem <KEY> to activate."
        )
        return jsonify({"status": "forbidden", "message": "No active license"}), 403
        
    # 2. Consume use if single_use
    if ltype == "single":
        consumed = consume_use(user_id)
        if not consumed:
            send_telegram_message(
                chat_id=int(user_id),
                text="❌ Failed to consume license. Make sure you have uses remaining."
            )
            return jsonify({"status": "forbidden", "message": "No uses remaining"}), 403
            
    # 3. Generate description
    try:
        username, output_file = generate_user_description(user_id)
        
        # 4. Send document to Telegram user!
        success = send_telegram_file(
            chat_id=int(user_id),
            filepath=output_file,
            caption=f"📝 Eldorado listing description for {username}!"
        )
        
        if success:
            # Send status update
            _, _, remaining = check_license(user_id)
            bal_str = "Lifetime ♾️" if ltype == "lifetime" else f"{remaining} use(s) remaining"
            send_telegram_message(
                chat_id=int(user_id),
                text=f"✅ Description generated successfully! Balance: {bal_str}."
            )
            
            # Clean up user's data files to save space
            try:
                user_dir = f"data/{user_id}"
                for f in os.listdir(user_dir):
                    os.remove(os.path.join(user_dir, f))
            except Exception:
                pass
                
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send file via Telegram"}), 500
            
    except Exception as e:
        logger.error(f"Error generating description: {e}", exc_info=True)
        send_telegram_message(
            chat_id=int(user_id),
            text=f"❌ Error generating description: {str(e)}"
        )
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    logger.info("Starting Flask server on port 5000...")
    flask_app.run(host='127.0.0.1', port=5000)

# Telegram Bot Handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} triggered /start")
    
    welcome_text = (
        "👋 **Welcome to DGowdru Description Bot!**\n\n"
        "Get Eldorado listing descriptions automatically straight from your Polygon phone!\n\n"
        "💳 **Pricing Plan:**\n"
        "• Single-use Key: 5 INR (One account generation)\n"
        "• Lifetime License: 1000 INR (Unlimited accounts)\n\n"
        "🔑 **How to get started:**\n"
        "1. Purchase a license key from the Admin.\n"
        "2. Redeem it using `/redeem <YOUR_KEY>`.\n"
        "3. Type `/mylink` to get your private Polygon URL.\n"
        "4. Set this URL in your Polygon app as the Backend/Proxy URL.\n"
        "5. Open Pokemon Go, and watch your description arrive here instantly!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    user_key = f"user_{user_id}"
    
    logger.info(f"User {user_id} triggered /status")
    
    if user_key not in db:
        await update.message.reply_text("❌ No active license found. Use `/redeem <KEY>` to activate.")
        return
        
    profile = db[user_key]
    ltype = profile.get("type", "single")
    if ltype == "lifetime":
        await update.message.reply_text("♾️ **License Type:** Lifetime (Unlimited access)\nStatus: Active ✅")
    else:
        uses = profile.get("uses_left", 0)
        await update.message.reply_text(f"🎫 **License Type:** Single-use\nRemaining Balance: {uses} account(s)\nStatus: Active ✅")

async def mylink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    user_key = f"user_{user_id}"
    
    logger.info(f"User {user_id} triggered /mylink")
    
    if user_key not in db:
        await update.message.reply_text("⚠️ You do not have an active license. Please redeem a key first.")
        return
        
    host = os.environ.get("RENDER_EXTERNAL_URL", "https://dgowdru.onrender.com")
    hook_url = f"{host}/hook/{user_id}"
    await update.message.reply_text(
        f"🔗 **Your Unique Polygon URL:**\n`{hook_url}`\n\n"
        "Set this as the Backend/Proxy URL in your Polygon settings.",
        parse_mode="Markdown"
    )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or f"User_{user_id}"
    
    logger.info(f"User {user_id} triggered /redeem")
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/redeem <KEY>`")
        return
        
    key = context.args[0].strip()
    await update.message.reply_text("Verifying key...")
    
    db = get_db()
    if key not in db:
        await update.message.reply_text("❌ Invalid License Key!")
        return
        
    record = db[key]
    key_type = record.get('type')
    
    if key_type == 'permanent':
        if record.get('telegram_id') is not None and record.get('telegram_id') != user_id:
            await update.message.reply_text("❌ This key is already registered to another Telegram account.")
            return
            
        db[key]['telegram_id'] = user_id
        db[key]['telegram_username'] = username
        db[f"user_{user_id}"] = {
            "type": "lifetime",
            "username": username,
            "uses_left": -1,
            "key": key
        }
        save_db(db)
        await update.message.reply_text("🎉 Successfully activated Permanent Lifetime License! Thank you.")
        
    elif key_type == 'single_use':
        if record.get('used', False):
            await update.message.reply_text("❌ This key has already been burned/used.")
            return
            
        db[key]['telegram_id'] = user_id
        db[key]['telegram_username'] = username
        db[key]['used'] = True
        
        user_key = f"user_{user_id}"
        user_profile = db.get(user_key, {
            "type": "single",
            "username": username,
            "uses_left": 0
        })
        user_profile["uses_left"] += 1
        user_profile["type"] = "single" if user_profile.get("type") != "lifetime" else "lifetime"
        db[user_key] = user_profile
        
        # Burn key
        del db[key]
        
        save_db(db)
        await update.message.reply_text(f"🎉 1-Use Key Accepted! Balance added. You now have {user_profile['uses_left']} uses left.")
    else:
        await update.message.reply_text("❌ Unsupported key type.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **DGowdru Bot Help Instructions:**\n\n"
        "1. Get a key from the owner/admin.\n"
        "2. Redeeming: Type `/redeem <key>` to add balance or lifetime access.\n"
        "3. Setup: Type `/mylink` to get your private URL.\n"
        "4. In the Polygon app settings on your phone, change the 'Backend URL' to your private URL.\n"
        "5. Start farming. When the account syncs and game loads, a `.txt` file containing the Eldorado listing description will be sent here automatically."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Admin Commands (check ADMIN_ID)
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied: Admin only.")
        return
        
    if not context.args or context.args[0].lower() not in ["lifetime", "single"]:
        await update.message.reply_text("❌ Usage: `/generate <lifetime|single>`")
        return
        
    gtype = context.args[0].lower()
    key = generate_key(gtype)
    
    await update.message.reply_text(f"Generating key of type: {gtype}...")
    add_key_to_db(key, gtype)
    
    await update.message.reply_text(f"🔑 **New Key Created:**\n`{key}`\n\nSend this key to the buyer.", parse_mode="Markdown")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied: Admin only.")
        return
        
    if not context.args:
        await update.message.reply_text("❌ Usage: `/revoke <KEY_OR_USER_ID>` (e.g. user_12345 or DGowdru-...)")
        return
        
    target = context.args[0].strip()
    db = get_db()
    
    if target in db:
        del db[target]
        save_db(db)
        await update.message.reply_text(f"✅ Revoked: {target} removed from licensing database.")
    else:
        user_key = target if target.startswith("user_") else f"user_{target}"
        if user_key in db:
            del db[user_key]
            save_db(db)
            await update.message.reply_text(f"✅ Revoked user profile: {user_key} removed.")
        else:
            await update.message.reply_text(f"❌ Target '{target}' not found in database.")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied: Admin only.")
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/addbalance <TELEGRAM_USER_ID> <AMOUNT>`")
        return
        
    target_id = context.args[0].strip()
    try:
        amount = int(context.args[1].strip())
    except ValueError:
        await update.message.reply_text("❌ Amount must be an integer.")
        return
        
    db = get_db()
    user_key = f"user_{target_id}"
    if user_key not in db:
        db[user_key] = {
            "type": "single",
            "username": f"User_{target_id}",
            "uses_left": 0
        }
    
    db[user_key]["uses_left"] = max(0, db[user_key].get("uses_left", 0) + amount)
    db[user_key]["type"] = "single" if db[user_key].get("type") != "lifetime" else "lifetime"
    save_db(db)
    
    await update.message.reply_text(f"✅ Added {amount} use(s) to user {target_id}. New balance: {db[user_key]['uses_left']} use(s).")

async def set_lifetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied: Admin only.")
        return
        
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setlifetime <TELEGRAM_USER_ID>`")
        return
        
    target_id = context.args[0].strip()
    db = get_db()
    user_key = f"user_{target_id}"
    
    if user_key not in db:
        db[user_key] = {
            "username": f"User_{target_id}"
        }
        
    db[user_key]["type"] = "lifetime"
    db[user_key]["uses_left"] = -1
    save_db(db)
    
    await update.message.reply_text(f"✅ Granted lifetime access to user {target_id}.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied: Admin only.")
        return
        
    db = get_db()
    user_profiles = {k: v for k, v in db.items() if k.startswith("user_")}
    
    if not user_profiles:
        await update.message.reply_text("No users registered yet.")
        return
        
    text = "📋 **Registered Users list:**\n\n"
    for k, profile in user_profiles.items():
        uid = k.replace("user_", "")
        utype = profile.get("type", "single")
        username = profile.get("username", "Unknown")
        balance = profile.get("uses_left", 0)
        bal_str = "Lifetime ♾️" if utype == "lifetime" else f"{balance} uses"
        text += f"• ID: `{uid}` (@{username}) | License: {utype.capitalize()} ({bal_str})\n"
        
    await update.message.reply_text(text, parse_mode="Markdown")

async def main_bot():
    global tg_application
    tg_application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Capture active event loop
    tg_application.loop = asyncio.get_event_loop()
    
    # Add User handlers
    tg_application.add_handler(CommandHandler("start", start))
    tg_application.add_handler(CommandHandler("status", status))
    tg_application.add_handler(CommandHandler("mylink", mylink))
    tg_application.add_handler(CommandHandler("redeem", redeem))
    tg_application.add_handler(CommandHandler("help", help_command))
    
    # Add Admin handlers
    tg_application.add_handler(CommandHandler("generate", generate))
    tg_application.add_handler(CommandHandler("revoke", revoke))
    tg_application.add_handler(CommandHandler("addbalance", add_balance))
    tg_application.add_handler(CommandHandler("setlifetime", set_lifetime))
    tg_application.add_handler(CommandHandler("listusers", list_users))
    
    # Start bot Updater
    logger.info("Initializing Telegram bot...")
    await tg_application.initialize()
    await tg_application.start()
    await tg_application.updater.start_polling()
    
    logger.info("Telegram long-polling bot is live!")
    
    # Run forever in event loop
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    # Start Flask Webserver in background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    # Run Telegram Bot asyncio loop
    asyncio.run(main_bot())
