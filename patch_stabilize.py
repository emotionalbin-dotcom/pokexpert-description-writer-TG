import os
import re

files_to_patch = ['parse_final_locked.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Uncomment authenticate
    content = content.replace('# authenticate()', 'authenticate()')

    # Add file stabilization wait function
    wait_func = """
def wait_for_file(filepath, timeout=300):
    import time
    for _ in range(timeout):
        if os.path.exists(filepath):
            try:
                size1 = os.path.getsize(filepath)
                time.sleep(0.5)
                size2 = os.path.getsize(filepath)
                if size1 > 0 and size1 == size2:
                    return True
            except:
                pass
        time.sleep(1)
    return False
"""

    if 'def wait_for_file' not in content:
        content = content.replace("import time\nprint('Waiting for Interceptor", wait_func + "\nprint('Waiting for Interceptor")

    # Replace the wait loop
    old_loop = """for i in range(300):
    if os.path.exists('inventory_raw.bin') and os.path.exists('player_debug.json'):
        break
    if i > 0 and i % 30 == 0:
        print(f'Still waiting... ({300 - i} seconds left). Please log in to the Pokemon Go Web Store.')
    time.sleep(1)"""
    
    new_loop = """
print('Waiting for player_debug.json...')
if not wait_for_file('player_debug.json'):
    print('[ERROR] player_debug.json failed to write.')
print('Waiting for inventory_raw.bin...')
if not wait_for_file('inventory_raw.bin'):
    print('[ERROR] inventory_raw.bin failed to write.')
"""

    content = content.replace(old_loop, new_loop)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
        
files_to_patch = ['parse_final_unlocked.py']
for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'def wait_for_file' not in content:
        content = content.replace("import time\nprint('Waiting for Interceptor", wait_func + "\nprint('Waiting for Interceptor")
    content = content.replace(old_loop, new_loop)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patch applied successfully.")
