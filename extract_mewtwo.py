import re

with open('inventory_decoded.txt', 'r') as f:
    content = f.read()

# We need to find the inventory_item_data -> pokemon_data
# In protoc output, it looks like:
# 3 {
#   1 {
#     ...
#     2: 150
#     ...
#   }
# }
# But because of indentation, we can just split by "3 {" and then look for "1 {" that contains "2: 150"

blocks = re.split(r'^\s*3 \{\s*$', content, flags=re.MULTILINE)
mewtwo_blocks = []

for block in blocks:
    if re.search(r'^\s*2: 150\s*$', block, re.MULTILINE):
        mewtwo_blocks.append(block)

print(f"Found {len(mewtwo_blocks)} Mewtwo blocks.")

# We want to dump all Mewtwo blocks to a file so we can inspect them!
with open('mewtwo_blocks.txt', 'w') as f:
    for i, block in enumerate(mewtwo_blocks):
        f.write(f"=== MEWTWO {i+1} ===\n")
        f.write("3 {\n")
        f.write(block)
        f.write("\n\n")
