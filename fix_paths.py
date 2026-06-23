import os, sys
with open('parse_final.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('parse_final_shared.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if 'protoc_path =' in line:
            f.write('    protoc_path = os.path.join(sys._MEIPASS, \'protoc.exe\') if hasattr(sys, \'_MEIPASS\') else \'protoc\'\n')
        elif 'inventory_raw.json' in line:
            f.write(line.replace('inventory_raw.json', 'inventory_raw.json'))
        else:
            f.write(line)
