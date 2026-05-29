#!/usr/bin/env python3
"""Fix the last remaining flash messages."""

import re

# Fix admin/routes.py
with open('/workspace/routes/admin/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 444
content = content.replace(
    'flash(f"✅ User\'{user.username}\' has been disabled.")',
    'flash(gettext(f"✅ User\'{user.username}\' has been disabled."))'
)

# Fix line 457
content = content.replace(
    'flash(f"✅ User\'{user.username}\' activated.")',
    'flash(gettext(f"✅ User\'{user.username}\' activated."))'
)

with open('/workspace/routes/admin/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed admin/routes.py")

# The social/routes.py uses t_() which is already a translation function
# The routes/users/routes.py line 285 uses a variable 'error' which should already be translated

print("Done!")
