import os
import re

files_to_patch = ['parse_final_locked.py', 'parse_final_unlocked.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Change the waiting condition
        content = re.sub(
            r"if os\.path\.exists\('inventory_raw\.bin'\):",
            "if os.path.exists('inventory_raw.bin') and os.path.exists('player_debug.json'):",
            content
        )

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
