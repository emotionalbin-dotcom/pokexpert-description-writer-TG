with open('parse_final_locked.py', 'r', encoding='utf-8') as f:
    locked = f.read()
with open('parse_final_unlocked.py', 'r', encoding='utf-8') as f:
    unlocked = f.read()

# Find the medals section in locked
start_mark = '# --- MEDALS SECTION (Platinum + Event only) ---'
end_mark = '# --- END MEDALS ---'

start = locked.find(start_mark)
end = locked.find(end_mark) + len(end_mark)
medals_block = locked[start:end]

# Replace in unlocked
old_medals_start = unlocked.find('# --- MEDALS SECTION ---')
if old_medals_start == -1:
    old_medals_start = unlocked.find('# --- MEDALS SECTION (Platinum')
old_medals_end = unlocked.find('# --- END MEDALS ---') + len('# --- END MEDALS ---')

if old_medals_start != -1 and old_medals_end > old_medals_start:
    unlocked = unlocked[:old_medals_start] + medals_block + unlocked[old_medals_end:]
    print('Replaced medals section in unlocked')
else:
    # Insert before closing summary
    insert_pt = unlocked.rfind("lines.append(\"\U0001f4b2")
    if insert_pt == -1:
        insert_pt = unlocked.rfind("lines.append(\"💲")
    if insert_pt == -1:
        insert_pt = unlocked.rfind("lines.append(\"💎")
    if insert_pt != -1:
        unlocked = unlocked[:insert_pt] + medals_block + '\n\n' + unlocked[insert_pt:]
        print(f'Inserted medals block at position {insert_pt}')
    else:
        print('Could not find position')

with open('parse_final_unlocked.py', 'w', encoding='utf-8') as f:
    f.write(unlocked)
print('Done')
