#!/usr/bin/env python3
"""
Script to add Flask-Babel translation tags to HTML templates.
Uses {{ _('text') }} for translating text in HTML files.
"""

import os
import re
from pathlib import Path

def is_already_translated(text):
    """Check if text is already wrapped in translation tags."""
    if '{{ _(' in text or "{% trans %}" in text:
        return True
    return False

def extract_english_text(match):
    """Extract English text from HTML tag content."""
    full_match = match.group(0)
    prefix = match.group(1)  # Opening tag part
    content = match.group(2)  # Text content
    suffix = match.group(3)  # Closing tag part
    
    # Skip if already translated
    if is_already_translated(content):
        return full_match
    
    # Skip if content looks like Jinja2 variable or template tag
    if '{{' in content or '{%' in content or content.strip().startswith('_'):
        return full_match
    
    # Skip very short content (likely symbols or single letters)
    if len(content.strip()) < 2:
        return full_match
    
    # Skip if content has no alphabetic characters
    if not any(c.isalpha() for c in content):
        return full_match
    
    # Wrap the content with translation tag
    return f"{prefix}{{{{ _('{content}') }}}}{suffix}"

def process_html_file(filepath):
    """Process a single HTML file and add translation tags."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0
    
    original_content = content
    changes_count = 0
    
    # Pattern 1: Text between > and < (tag content)
    # Match opening tag >, content, closing <
    pattern1 = r'(>[^{}]*?)((?:[A-Za-z][A-Za-z0-9\s\-\.\'\!\?\,\:\;\(\)]{1,200}?))(<)'
    
    def replace_pattern1(match):
        nonlocal changes_count
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        
        # Skip if already translated
        if '_(' in content or '{% trans' in content:
            return match.group(0)
        
        # Skip Jinja2 expressions
        if '{{' in content or '{%' in content:
            return match.group(0)
        
        # Skip if no letters
        if not any(c.isalpha() for c in content):
            return match.group(0)
        
        # Skip very short strings
        if len(content.strip()) < 2:
            return match.group(0)
        
        # Skip common false positives
        skip_patterns = [
            r'^\s*$',  # Empty
            r'^[\s\-]+$',  # Only spaces/dashes
            r'^\d+$',  # Only numbers
        ]
        for skip in skip_patterns:
            if re.match(skip, content.strip()):
                return match.group(0)
        
        changes_count += 1
        return f"{prefix}{{{{ _('{content}') }}}}{suffix}"
    
    content = re.sub(pattern1, replace_pattern1, content)
    
    # Pattern 2: title, placeholder, alt attributes
    attr_pattern = r'((?:title|placeholder|alt|aria-label)\s*=\s*[\"\'])([^\"\'\{\}]+?)([\"\'])'
    
    def replace_attr(match):
        nonlocal changes_count
        prefix = match.group(1)
        attr_value = match.group(2)
        suffix = match.group(3)
        
        # Skip if already translated
        if '_(' in attr_value:
            return match.group(0)
        
        # Skip Jinja2 expressions
        if '{{' in attr_value or '{%' in attr_value:
            return match.group(0)
        
        # Skip if no letters
        if not any(c.isalpha() for c in attr_value):
            return match.group(0)
        
        changes_count += 1
        return f'{prefix}{{{{ _("{attr_value}") }}}}{suffix}'
    
    content = re.sub(attr_pattern, replace_attr, content)
    
    # Write back if changed
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_count
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return 0
    
    return 0

def main():
    templates_dir = Path('templates')
    if not templates_dir.exists():
        print("Templates directory not found!")
        return
    
    html_files = list(templates_dir.rglob('*.html'))
    print(f"Found {len(html_files)} HTML files")
    
    total_changes = 0
    processed_files = 0
    
    for filepath in html_files:
        changes = process_html_file(filepath)
        if changes > 0:
            print(f"✓ {filepath}: {changes} translations added")
            total_changes += changes
            processed_files += 1
    
    print(f"\n=== Summary ===")
    print(f"Files processed: {processed_files}/{len(html_files)}")
    print(f"Total translations added: {total_changes}")

if __name__ == '__main__':
    main()
