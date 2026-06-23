with open('Hdsgwhjhw.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '📖' in line or '✨' in line:
        safe_line = line.encode('ascii', 'ignore').decode('ascii').strip()
        if safe_line:
            print(f"Line {i}: {safe_line}")
