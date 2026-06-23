import re

with open('parse_final_locked.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add fast_tms and charged_tms definitions right after elite_charge_tm
content = content.replace('elite_charge_tm = items.get("1204", 0)', 'elite_charge_tm = items.get("1204", 0)\nfast_tms = items.get("1201", 0)\ncharged_tms = items.get("1202", 0)')

with open('parse_final_locked.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added missing TM definitions!")
