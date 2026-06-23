import json
import os
import sys

# Legendary & Mythical sets for fast lookup
legendary_names = {'ARTICUNO', 'ZAPDOS', 'MOLTRES', 'MEWTWO', 'RAIKOU', 'ENTEI', 'SUICUNE', 'LUGIA', 'HO_OH', 'REGIROCK', 'REGICE', 'REGISTEEL', 'LATIAS', 'LATIOS', 'KYOGRE', 'GROUDON', 'RAYQUAZA', 'UXIE', 'MESPRIT', 'AZELF', 'DIALGA', 'PALKIA', 'HEATRAN', 'REGIGIGAS', 'GIRATINA', 'CRESSELIA', 'COBALION', 'TERRAKION', 'VIRIZION', 'TORNADUS', 'THUNDURUS', 'RESHIRAM', 'ZEKROM', 'LANDORUS', 'KYUREM', 'XERNEAS', 'YVELTAL', 'ZYGARDE', 'TAPU_KOKO', 'TAPU_LELE', 'TAPU_BULU', 'TAPU_FINI', 'COSMOG', 'COSMOEM', 'SOLGALEO', 'LUNALA', 'NIHILEGO', 'BUZZWOLE', 'PHEROMOSA', 'XURKITREE', 'CELESTEELA', 'KARTANA', 'GUZZLORD', 'NECROZMA', 'POIPOLE', 'NAGANADEL', 'STAKATAKA', 'BLACEPHALON', 'ZACIAN', 'ZAMAZENTA', 'ETERNATUS', 'REGIELEKI', 'REGIDRAGO', 'ENAMORUS'}
mythical_names = {'MEW', 'CELEBI', 'JIRACHI', 'DEOXYS', 'MANAPHY', 'PHIONE', 'DARKRAI', 'SHAYMIN', 'ARCEUS', 'VICTINI', 'KELDEO', 'MELOETTA', 'GENESECT', 'DIANCIE', 'HOOPA', 'VOLCANION', 'MAGEARNA', 'MARSHADOW', 'ZERAORA', 'MELTAN', 'MELMETAL', 'ZARUDE'}

def evaluate_term(term, p):
    term = term.strip().lower()
    if not term:
        return True
        
    # Handle negation (!)
    if term.startswith('!'):
        return not evaluate_term(term[1:], p)
        
    name = p.get('pokemon_id', '').lower()
    atk = p.get('individual_attack', 0)
    def_ = p.get('individual_defense', 0)
    sta = p.get('individual_stamina', 0)
    total_iv = atk + def_ + sta
    iv_percent = total_iv / 45.0
    
    display = p.get('pokemon_display', {})
    form = display.get('form', '').lower()
    alignment = display.get('alignment', '')
    
    # 1. IV Star Ratings
    if term == '4*': return atk == 15 and def_ == 15 and sta == 15
    if term == '3*': return iv_percent >= 0.822 and total_iv < 45
    if term == '2*': return iv_percent >= 0.667 and iv_percent < 0.822
    if term == '1*': return iv_percent >= 0.511 and iv_percent < 0.667
    if term == '0*': return iv_percent < 0.511
    
    # 2. Status / Tags
    if term == 'shiny': return display.get('shiny', False)
    if term == 'costume': return display.get('costume', 0) > 0
    if term == 'shadow': return alignment == 'ALIGNMENT_SHADOW' or 'shadow' in form
    if term == 'purified': return alignment == 'ALIGNMENT_PURIFIED' or 'purified' in form
    if term == 'lucky': return p.get('is_lucky', False)
    
    # 3. Rarity
    if term == 'legendary': return name.upper() in legendary_names
    if term == 'mythical': return name.upper() in mythical_names
    
    # 4. Special Backgrounds
    if term == 'background': return len(p.get('origin_events', [])) > 0
    if term == 'locationcards': return display.get('location_card', {}).get('location_card', '') != ''
    if term == 'dynamax': return 'dynamax' in form
    if term == 'gigantamax': return 'gigantamax' in form
    
    # 5. Fallback check for exact name match (e.g. "pikachu")
    if name == term: return True
    
    return False

def evaluate_and_group(group_str, p):
    # All terms separated by '&' MUST be true
    terms = group_str.split('&')
    for term in terms:
        if not evaluate_term(term, p):
            return False
    return True

def matches_query(query, p):
    # Groups separated by ',' are OR conditions. If ANY group is true, it's a match.
    or_groups = query.split(',')
    for group in or_groups:
        if evaluate_and_group(group, p):
            return True
    return False

def search_inventory(query, filepath='inventory_raw.json'):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    results = [p for p in data if matches_query(query, p)]
    return results

if __name__ == '__main__':
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search_inventory(query)
        print(f"\\n--- SEARCH RESULTS FOR: [{query}] ---")
        print(f"Total Matches: {len(results)}\\n")
        
        for p in results:
            cp = p.get('cp', 0)
            name = p.get('pokemon_id', 'UNKNOWN').replace('_', ' ').title()
            atk = p.get('individual_attack', 0)
            def_ = p.get('individual_defense', 0)
            sta = p.get('individual_stamina', 0)
            
            tags = []
            if p.get('pokemon_display', {}).get('shiny', False): tags.append("✨ Shiny")
            if len(p.get('origin_events', [])) > 0: tags.append("🎨 Background")
            if p.get('pokemon_display', {}).get('location_card', {}).get('location_card', '') != '': tags.append("📍 Loc Card")
            
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"- CP {cp} {name} (IV: {atk}/{def_}/{sta}){tag_str}")
    else:
        print("Usage: python pogo_search.py <query>")
        print('Example: python pogo_search.py "shiny & legendary"')
