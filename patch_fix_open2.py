import os

files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Revert ALL bad replacements
        content = content.replace(
            'open("inventory_decoded.txt", "inventory_raw.txt",',
            'open("inventory_decoded.txt",'
        )

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
