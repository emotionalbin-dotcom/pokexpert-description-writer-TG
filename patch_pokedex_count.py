import os

files_to_patch = ['parse_final.py', 'parse_final_shared.py', 'parse_final_locked.py', 'parse_final_locked_test.py']

for filename in files_to_patch:
    if not os.path.exists(filename):
        continue
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        skip_indent = False
        for line in lines:
            if "if first_line.startswith('3 {'):" in line:
                skip_indent = True
                continue
            
            if skip_indent:
                if 'if \'1:\' in match:' in line:
                    new_lines.append(line.replace('        if', '    if', 1))
                elif 'pokedex_unique += 1' in line:
                    new_lines.append(line.replace('            pokedex_unique', '        pokedex_unique', 1))
                elif 'if re.search' in line:
                    new_lines.append(line.replace('            if', '        if', 1))
                elif 'pokedex_shiny += 1' in line:
                    new_lines.append(line.replace('                pokedex_shiny', '            pokedex_shiny', 1))
                    skip_indent = False # End of block
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("".join(new_lines))
        print(f"Patched {filename} successfully!")
    except Exception as e:
        print(f"Failed {filename}: {e}")
