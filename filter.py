import json
import os
from collections import Counter

def to_bold_sans(text):
    # Mapping for mathematical sans-serif bold characters used in the template
    # This gives that exact "𝗟𝗲𝘃𝗲𝗹 𝟳𝟯" look
    mapping = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚',
        'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡',
        'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨',
        'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴',
        'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻',
        'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂',
        'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱',
        '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
    return "".join(mapping.get(c, c) for c in str(text))

def main():
    if not os.path.exists('inventory_raw.json'):
        print("Error: inventory_raw.json not found. Make sure the Node script has dumped the data.")
        return
        
    with open('inventory_raw.json', 'r', encoding='utf-8') as f:
        inventory = json.load(f)
        
    legendary_names = {'ARTICUNO', 'ZAPDOS', 'MOLTRES', 'MEWTWO', 'RAIKOU', 'ENTEI', 'SUICUNE', 'LUGIA', 'HO_OH', 'REGIROCK', 'REGICE', 'REGISTEEL', 'LATIAS', 'LATIOS', 'KYOGRE', 'GROUDON', 'RAYQUAZA', 'UXIE', 'MESPRIT', 'AZELF', 'DIALGA', 'PALKIA', 'HEATRAN', 'REGIGIGAS', 'GIRATINA', 'CRESSELIA', 'COBALION', 'TERRAKION', 'VIRIZION', 'TORNADUS', 'THUNDURUS', 'RESHIRAM', 'ZEKROM', 'LANDORUS', 'KYUREM', 'XERNEAS', 'YVELTAL', 'ZYGARDE', 'TAPU_KOKO', 'TAPU_LELE', 'TAPU_BULU', 'TAPU_FINI', 'COSMOG', 'COSMOEM', 'SOLGALEO', 'LUNALA', 'NIHILEGO', 'BUZZWOLE', 'PHEROMOSA', 'XURKITREE', 'CELESTEELA', 'KARTANA', 'GUZZLORD', 'NECROZMA', 'POIPOLE', 'NAGANADEL', 'STAKATAKA', 'BLACEPHALON', 'ZACIAN', 'ZAMAZENTA', 'ETERNATUS', 'REGIELEKI', 'REGIDRAGO', 'ENAMORUS'}
    mythical_names = {'MEW', 'CELEBI', 'JIRACHI', 'DEOXYS', 'MANAPHY', 'PHIONE', 'DARKRAI', 'SHAYMIN', 'ARCEUS', 'VICTINI', 'KELDEO', 'MELOETTA', 'GENESECT', 'DIANCIE', 'HOOPA', 'VOLCANION', 'MAGEARNA', 'MARSHADOW', 'ZERAORA', 'MELTAN', 'MELMETAL', 'ZARUDE'}
    
    # Counters
    stats = {
        'legendary': 0, 'shiny': 0, 'hundo': 0, 'shundo': 0,
        'dual_move': 0, 'hatched_shiny': 0, 'costume_shiny': 0,
        'dynamax': 0, 'gigantamax': 0, 'loc_card_shiny': 0,
        'spec_bg_shiny': 0, 'hundo_leg': 0, 'shiny_leg': 0
    }
    
    spec_shiny_list = []
    spec_hundo_list = []
    
    for p in inventory:
        name = p.get('pokemon_id', 'UNKNOWN')
        atk = p.get('individual_attack', 0)
        def_ = p.get('individual_defense', 0)
        sta = p.get('individual_stamina', 0)
        
        display = p.get('pokemon_display', {})
        is_shiny = display.get('shiny', False)
        is_hundo = (atk == 15 and def_ == 15 and sta == 15)
        is_leg = name in legendary_names or name in mythical_names
        
        has_spec_bg = len(p.get('origin_events', [])) > 0
        has_loc_card = display.get('location_card', {}).get('location_card', '') != ''
        
        if is_leg: stats['legendary'] += 1
        if is_shiny: stats['shiny'] += 1
        if is_hundo: stats['hundo'] += 1
        if is_shiny and is_hundo: stats['shundo'] += 1
        if 'move3' in p: stats['dual_move'] += 1
        
        if is_shiny and display.get('costume', 0) > 0: stats['costume_shiny'] += 1
        if is_shiny and p.get('pokeball', 1) == 0: stats['hatched_shiny'] += 1
        
        form_str = str(display.get('form', '')).upper()
        if 'DYNAMAX' in form_str: stats['dynamax'] += 1
        if 'GIGANTAMAX' in form_str: stats['gigantamax'] += 1
        
        if is_shiny and has_loc_card: stats['loc_card_shiny'] += 1
        if is_shiny and has_spec_bg: stats['spec_bg_shiny'] += 1
        
        if is_hundo and is_leg: stats['hundo_leg'] += 1
        if is_shiny and is_leg: stats['shiny_leg'] += 1
        
        nice_name = name.replace('_', ' ').title()
        
        # Build lists
        if is_shiny and is_leg and (has_loc_card or has_spec_bg):
            type_str = "Location Card" if has_loc_card else "Special Background"
            spec_shiny_list.append(f"✨ {{count}} {to_bold_sans(type_str + ' Shiny ' + nice_name)}")
            
        if is_hundo and is_leg and (has_loc_card or has_spec_bg):
            type_str = "Location Card" if has_loc_card else "Special Background"
            spec_hundo_list.append(f"💯 {to_bold_sans('Hundo ' + type_str + ' ' + nice_name)}")
            
    # Aggregate lists
    def aggregate(items):
        counts = Counter(items)
        out = []
        for template, count in counts.items():
            out.append(template.format(count=to_bold_sans(str(count))))
        return "\n".join(out)
        
    shiny_bg_str = aggregate(spec_shiny_list)
    hundo_bg_str = aggregate(spec_hundo_list)

    # Build Template
    output = f"""✨ {to_bold_sans("Level ?? Account")} ✨

• {to_bold_sans("Stacked Account")}
• {to_bold_sans("PvP Account")}
• {to_bold_sans("Best Medals")}
• {to_bold_sans("Powerful High CP")}
• {to_bold_sans("Event Played Account")}

━━━━━━━━━━━━━━━━━━

🌟 {to_bold_sans("Account Overview")} 🌟

🔱 {to_bold_sans(stats['legendary'])} {to_bold_sans("Legendary")}
✨ {to_bold_sans(stats['shiny'])} {to_bold_sans("Shiny")}
💯 {to_bold_sans(stats['hundo'])} {to_bold_sans("Hundo")}
🌟 {to_bold_sans(stats['shundo'])} {to_bold_sans("Shundo")}
⚔️ {to_bold_sans(stats['dual_move'])} {to_bold_sans("Dual Move")}
🥚 {to_bold_sans(stats['hatched_shiny'])} {to_bold_sans("Hatched Shiny")}
🎭 {to_bold_sans(stats['costume_shiny'])} {to_bold_sans("Costume Shiny")}

━━━━━━━━━━━━━━━━━━

🏆 {to_bold_sans(stats['hundo_leg'])} {to_bold_sans("Hundo Legendary, Mythical & Ultra Beasts")}
✨ {to_bold_sans(stats['shiny_leg'])} {to_bold_sans("Shiny Legendary, Mythical & Ultra Beasts")}

━━━━━━━━━━━━━━━━━━

💎 {to_bold_sans("Overall a Stacked PvP & Collectible Account")}
💎 {to_bold_sans("Rare Event Exclusives")}
💎 {to_bold_sans("High-End Shiny Collection")}
💎 {to_bold_sans("Massive Stardust & Resources")}
💎 {to_bold_sans("Ready for PvP, Raids & Collecting")}

━━━━━━━━━━━━━━━━━━

🔥 {to_bold_sans("Don't Just See — Buy Now!")} 🔥

📩 {to_bold_sans("For Sale")}
💬 {to_bold_sans("Message @[YOUR_USERNAME] To Purchase.")}
"""
    
    with open('eldorado_final_listing.txt', 'w', encoding='utf-8') as f:
        f.write(output)
        
    print("✅ Created eldorado_final_listing.txt successfully!")

if __name__ == '__main__':
    main()
