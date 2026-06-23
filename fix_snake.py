with open('parse_final_shared.py', 'r', encoding='utf-8') as f: text = f.read()
text = text.replace('Snake Form Zygarde checked below', 'REMOVED_LINE')
with open('parse_final_shared.py', 'w', encoding='utf-8') as f: f.write(text)