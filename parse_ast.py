import sys

def parse_protoc_output(lines):
    root = []
    stack = [root]
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped: continue
        
        if line_stripped.endswith('{'):
            # It's a nested message
            key = line_stripped[:-1].strip()
            new_node = {'_key': key, '_children': []}
            stack[-1].append(new_node)
            stack.append(new_node['_children'])
        elif line_stripped == '}':
            stack.pop()
        else:
            # It's a field
            if ':' in line_stripped:
                k, v = line_stripped.split(':', 1)
                stack[-1].append({'_key': k.strip(), '_val': v.strip()})
    
    return root

with open('inventory_decoded.txt', 'r') as f:
    lines = f.readlines()

ast = parse_protoc_output(lines)

# Find all pokemon_data (inside inventory_item_data -> pokemon_data)
# Structure: 2 -> 1 (repeated) -> 3 -> 1
pokemon_datas = []

for msg_root in ast:
    if msg_root.get('_key') == '2' and '_children' in msg_root:
        for msg_item in msg_root['_children']:
            if msg_item.get('_key') == '1' and '_children' in msg_item:
                for msg_item_data in msg_item['_children']:
                    if msg_item_data.get('_key') == '3' and '_children' in msg_item_data:
                        for msg_pokemon in msg_item_data['_children']:
                            if msg_pokemon.get('_key') == '1' and '_children' in msg_pokemon:
                                pokemon_datas.append(msg_pokemon)

def find_field(msg_list, key):
    for item in msg_list:
        if item.get('_key') == str(key):
            return item
    return None

def print_block(msg_list, indent=0):
    for item in msg_list:
        if '_val' in item:
            print("  " * indent + f"{item['_key']}: {item['_val']}")
        else:
            print("  " * indent + f"{item['_key']} {{")
            print_block(item['_children'], indent + 1)
            print("  " * indent + "}")

# Find Mewtwos
shiny_mewtwos = []
for p in pokemon_datas:
    f2 = find_field(p['_children'], 2)
    if f2 and f2.get('_val') == '150':
        # It's a Mewtwo!
        # Check if shiny (tag 36 -> 6: 1)
        f36 = find_field(p['_children'], 36)
        is_shiny = False
        if f36 and '_children' in f36:
            f6 = find_field(f36['_children'], 6)
            if f6 and f6.get('_val') == '1':
                is_shiny = True
        
        if is_shiny:
            shiny_mewtwos.append(p)

print(f"Found {len(shiny_mewtwos)} shiny Mewtwos.")
for i, m in enumerate(shiny_mewtwos):
    print(f"\n--- Shiny Mewtwo {i+1} ---")
    print_block(m['_children'])
