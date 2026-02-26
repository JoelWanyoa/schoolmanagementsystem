import os
import re
import json

def audit_templates():
    view_files = [
        'dashboard/views.py',
        'dashboard/views2.py',
        'core/views.py'
    ]
    templates_dir = 'templates'
    missing = []
    
    for view_file in view_files:
        if not os.path.exists(view_file):
            print(f"Skipping {view_file} (not found)")
            continue
            
        print(f"Auditing {view_file}...")
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all render calls
        # render(request, 'template.html', ...)
        matches = re.finditer(r'render\(request,\s*[\'"]([^\'"]+\.html)[\'"]', content)
        
        seen_in_this_file = set()
        for match in matches:
            template_path = match.group(1)
            if template_path in seen_in_this_file:
                continue
            seen_in_this_file.add(template_path)
            
            full_path = os.path.join(templates_dir, template_path.replace('/', os.sep))
            if not os.path.exists(full_path):
                # Find the view name
                # Look backwards from the match for the nearest 'def '
                block_before = content[:match.start()]
                view_name_match = re.findall(r'def\s+(\w+)\(', block_before)
                view_name = view_name_match[-1] if view_name_match else "Unknown"
                
                missing.append({
                    'file': view_file,
                    'view': view_name,
                    'template': template_path
                })
                
    return missing

if __name__ == "__main__":
    results = audit_templates()
    with open('missing_templates_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Found {len(results)} missing templates.")
    for r in results:
        print(f"[{r['view']}] -> {r['template']}")
