files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace('level = "73"', 'level = "???"')

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
