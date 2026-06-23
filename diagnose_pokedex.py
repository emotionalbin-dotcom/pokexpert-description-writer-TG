"""
DIAGNOSTIC SCRIPT - Run this AFTER intercepting one account (after inventory_decoded.txt is created).
It will tell us exactly what the Pokedex blocks look like so we can fix the regex.
"""
import re
import os
import sys

if not os.path.exists("inventory_decoded.txt"):
    print("[ERROR] inventory_decoded.txt not found!")
    print("Please run the interceptor first, then run this script.")
    input("Press Enter to exit...")
    sys.exit(1)

with open("inventory_decoded.txt", "r", encoding="utf-8", errors="replace") as f:
    full_content = f.read()

print(f"File size: {len(full_content)} characters")
print(f"Total lines: {full_content.count(chr(10))}")
print()

# Show the first 50 lines to understand the top-level structure
lines = full_content.split('\n')
print("=== FIRST 30 LINES ===")
for i, line in enumerate(lines[:30]):
    print(f"{i:4}: {repr(line)}")

print()
print("=== SEARCHING FOR POKEDEX MARKERS ===")
# Look for any line containing "pokedex" (case insensitive)
for i, line in enumerate(lines):
    if 'pokedex' in line.lower() or '  3 {' == line.strip() or '  3 {' == line:
        print(f"Line {i}: {repr(line)}")
        # Print context
        for j in range(max(0, i-1), min(len(lines), i+10)):
            print(f"  {j}: {repr(lines[j])}")
        print()
        if i > 50:  # Only show first few hits
            break

print()
print("=== TESTING REGEX PATTERNS ===")

# Current pattern
m1 = re.findall(r'  3 \{\n    .*?    3 \{\n(.*?)    \}\n  \}', full_content, re.DOTALL)
print(f"Current regex matches: {len(m1)}")

# Try broader patterns
m2 = re.findall(r'pokedex_id:\s*(\d+)', full_content)
print(f"'pokedex_id:' pattern: {len(m2)} matches")

m3 = re.findall(r'3:\s*\{', full_content)
print(f"'3: {{' pattern: {len(m3)} matches")

# Show a sample of what IS in the file around "3 {" blocks
idx = full_content.find('  3 {')
if idx == -1:
    idx = full_content.find('3: {')
if idx == -1:
    idx = full_content.find('3 {')
    
if idx != -1:
    print(f"\nFound potential block at index {idx}, showing 500 chars around it:")
    print(repr(full_content[max(0,idx-100):idx+400]))
else:
    print("\nNo '3 {' block found at all! Showing first 2000 chars of file:")
    print(repr(full_content[:2000]))

input("\nPress Enter to exit...")
