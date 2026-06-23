import os
import re

files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Initialize username
        if 'username = "Account"' not in content:
            content = content.replace('stardust = "???"', 'stardust = "???"\nusername = "Account"')

        # 2. Extract username
        if 'username = player_data.get("name", "Account")' not in content:
            content = content.replace('player_data = player_debug.get("player", {})', 'player_data = player_debug.get("player", {})\n              username = player_data.get("name", "Account")')

        # 3. Replace output file writing
        old_output = '''with open("eldorado_listings.txt", "w", encoding="utf-8") as f:
    f.write("\\r\\n".join(lines))

print("Results written to eldorado_listings.txt!")'''
        
        new_output = '''output_file = f"{username}.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\\r\\n".join(lines))

print(f"Results written to {output_file}!")

# Clean up temp files
import glob
temp_files = [
    "inventory_raw.bin", "inventory_raw.json", "inventory_decoded.txt",
    "player_debug.json", "player_raw.json", "raid_state.json",
    "eldorado_organized.txt", "eldorado_summary.txt", "eldorado_listings.txt"
]
for tf in temp_files:
    if os.path.exists(tf):
        try:
            os.remove(tf)
        except Exception:
            pass
'''
        content = content.replace(old_output, new_output)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
