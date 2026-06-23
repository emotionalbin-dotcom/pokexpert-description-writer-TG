import os

files_to_patch = ['parse_final_locked.py', 'parse_final_unlocked.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Wyrdeer, Kleavor, Ursaluna are NOT legendaries.
    content = content.replace('"898", "899", "900", "901", "905",', '"898", "905",')
    # If the original string had different spacing
    content = content.replace('"899", ', '')
    content = content.replace('"900", ', '')
    content = content.replace('"901", ', '')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patch applied successfully.")
