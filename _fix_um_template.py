import re

path = r'templates\admin\user_management.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Join any {{ ... }} that are split across lines
# Pattern: {{ at end of a line (with optional whitespace), rest on next line(s)
def join_split_tags(text):
    # Keep joining lines where {{ has no matching }} yet
    result = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Count unmatched {{ 
        opens = line.count('{{')
        closes = line.count('}}')
        if opens > closes:
            # Need to join with next line(s)
            merged = line.rstrip('\r')
            i += 1
            while i < len(lines) and merged.count('{{') > merged.count('}}'):
                merged = merged + ' ' + lines[i].strip().rstrip('\r')
                i += 1
            result.append(merged)
        else:
            result.append(line.rstrip('\r'))
            i += 1
    return '\n'.join(result)

fixed = join_split_tags(text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed)

# Verify
for i, line in enumerate(fixed.split('\n'), 1):
    if '{{' in line and '}}' not in line:
        print(f'Still split at L{i}: {line.strip()[:100]}')

print('Done. Spot-checking fixed lines:')
for i, line in enumerate(fixed.split('\n'), 1):
    if 'get_full_name' in line or 'first_name' in line:
        print(f'  L{i}: {line.strip()[:120]}')
