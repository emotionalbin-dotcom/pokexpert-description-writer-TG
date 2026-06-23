import os

files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if 'username = player_data.get("name", "Account")' in line:
                # Find the indentation of the previous line (which should be player_data = ...)
                prev_line = new_lines[-1]
                indent = len(prev_line) - len(prev_line.lstrip())
                new_lines.append(" " * indent + 'username = player_data.get("name", "Account")\n')
            else:
                new_lines.append(line)

        # Let's also add inventory_raw.txt to the cleanup list if it's not there!
        content = "".join(new_lines)
        if '"inventory_raw.txt"' not in content:
            content = content.replace('"inventory_decoded.txt",', '"inventory_decoded.txt", "inventory_raw.txt",')

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
