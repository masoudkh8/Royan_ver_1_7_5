#!/usr/bin/env python3
"""Fix remaining flash messages that weren't wrapped."""

import re

files_to_fix = [
    '/workspace/routes/users/routes.py',
]

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix line 285: flash(error) where error is a variable - skip this one
    # It's already a variable, not a string literal
    
    # Fix line 384: flash(f"❌ Your account is locked...")
    content = re.sub(
        r'flash\(f\"❌ Your account is locked until \{user\.locked_until\.strftime\(.*?\)\} due to failed attempts\.\"\)',
        r'flash(gettext(f"❌ Your account is locked until {user.locked_until.strftime(\'%Y-%m-%d %H:%M\')} due to failed attempts."))',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed {filepath}")
    else:
        print(f"- No changes for {filepath}")

print("Done!")
