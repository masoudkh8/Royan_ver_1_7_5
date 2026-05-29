#!/usr/bin/env python3
"""
Script to add translation tags to flash messages and other strings in Python files.
This script will:
1. Add gettext import to files that use flash() without translation
2. Wrap flash message strings with _() for translation
"""

import os
import re
from pathlib import Path

def get_python_files(directory):
    """Get all Python files in the routes directory."""
    py_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files

def check_has_gettext_import(content):
    """Check if file already has gettext import."""
    patterns = [
        r'from flask_babel.*import.*gettext',
        r'from flask_babel.*import.*_ as gettext',
        r'import gettext',
        r'from flask_babel import.*_',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def add_gettext_import(content):
    """Add gettext import after flask imports."""
    # Check if already has import
    if check_has_gettext_import(content):
        return content
    
    # Try to find flask_babel import and add gettext
    if 'from flask_babel import' in content:
        # Add gettext to existing flask_babel import
        content = re.sub(
            r'(from flask_babel import [^\n]+)',
            lambda m: m.group(1).replace(')', ', gettext)') if ')' in m.group(1) else m.group(1) + ', gettext',
            content
        )
        return content
    
    # Add new import after flask imports
    lines = content.split('\n')
    new_lines = []
    added = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if not added and (line.startswith('from flask ') or line.startswith('import flask')):
            # Find the last flask import line
            if i + 1 < len(lines) and not (lines[i+1].startswith('from flask ') or lines[i+1].startswith('import flask')):
                new_lines.append('from flask_babel import gettext')
                added = True
    
    if not added:
        # Add at the beginning after other imports
        for i, line in enumerate(lines):
            if line.startswith('from flask_babel'):
                if 'gettext' not in line:
                    new_lines[i] = line.replace(')', ', gettext)')
                added = True
                break
    
    if not added:
        # Just add it after the first import block
        new_lines.insert(0, 'from flask_babel import gettext')
    
    return '\n'.join(new_lines)

def wrap_flash_messages(content):
    """Wrap flash message strings with gettext."""
    # Pattern to match flash() calls with string literals
    # Matches: flash("message", "category") or flash('message') or flash(f"message {var}")
    
    def replace_flash(match):
        full_match = match.group(0)
        prefix = match.group(1)  # flash(
        
        # Get the content inside flash()
        inner = match.group(2)
        
        # Split by comma to separate message from category
        parts = []
        current = ""
        paren_depth = 0
        bracket_depth = 0
        in_string = False
        string_char = None
        
        for char in inner:
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and (not current or current[-1] != '\\'):
                    in_string = False
                    string_char = None
            
            if char == '(' :
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            
            if char == ',' and paren_depth == 0 and bracket_depth == 0 and not in_string:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            parts.append(current.strip())
        
        if not parts:
            return full_match
        
        # Process the first part (the message)
        message = parts[0]
        
        # Skip if already wrapped with gettext/_/t_
        if re.match(r'^[_\(t]', message.strip()):
            return full_match
        
        # Skip if it's a variable or function call (not a string literal)
        if not (message.strip().startswith('"') or message.strip().startswith("'") or 
                message.strip().startswith('f"') or message.strip().startswith("f'")):
            return full_match
        
        # Wrap the message with gettext()
        wrapped_message = f"gettext({message})"
        
        # Reconstruct the flash call
        if len(parts) > 1:
            rest = ', '.join(parts[1:])
            return f"{prefix}{wrapped_message}, {rest}"
        else:
            return f"{prefix}{wrapped_message}"
    
    # Match flash( followed by content until closing )
    # This is a simplified pattern - may need adjustment
    pattern = r'(flash\s*\()([^)]*(?:\)[^)]*)*?)\)'
    
    # Better approach: process line by line
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'flash(' in line and ('\"' in line or "'" in line):
            # Check if already has gettext
            if 'gettext(' in line or re.search(r'flash\s*\(\s*[_t]\(', line):
                new_lines.append(line)
                continue
            
            # Simple replacement for common patterns
            # Pattern 1: flash("message", "category")
            line = re.sub(
                r'flash\s*\(\s*([\"\'].*?[\"\'])\s*,',
                r'flash(gettext(\1),',
                line
            )
            
            # Pattern 2: flash("message") - single argument
            line = re.sub(
                r'flash\s*\(\s*([\"\'][^\"\']*?[\"\'])\s*\)',
                r'flash(gettext(\1))',
                line
            )
            
            # Pattern 3: flash(f"message {var}", "category")
            line = re.sub(
                r'flash\s*\(\s*(f[\"\'].*?[\"\'])\s*,',
                r'flash(gettext(\1),',
                line
            )
            
            # Pattern 4: flash(f"message {var}")
            line = re.sub(
                r'flash\s*\(\s*(f[\"\'][^\"\']*?[\"\'])\s*\)',
                r'flash(gettext(\1))',
                line
            )
            
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def process_file(filepath):
    """Process a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file has flash() calls
        if 'flash(' not in content:
            return False, "No flash calls"
        
        # Add gettext import if needed
        content = add_gettext_import(content)
        
        # Wrap flash messages
        content = wrap_flash_messages(content)
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Modified"
        else:
            return False, "No changes needed"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    routes_dir = '/workspace/routes'
    
    print("Scanning Python files in routes directory...")
    py_files = get_python_files(routes_dir)
    
    print(f"Found {len(py_files)} Python files")
    
    modified_count = 0
    error_count = 0
    
    for filepath in sorted(py_files):
        success, message = process_file(filepath)
        if success:
            modified_count += 1
            print(f"✓ {filepath}: {message}")
        elif message.startswith("Error"):
            error_count += 1
            print(f"✗ {filepath}: {message}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files modified: {modified_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total files processed: {len(py_files)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
