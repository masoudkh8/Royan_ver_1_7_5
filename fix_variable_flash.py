#!/usr/bin/env python3
"""Fix flash with variable - the error strings are already defined above."""

with open('/workspace/routes/users/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The errors list contains string literals that should be translated at source
# Let's wrap each error.append() with gettext

# Replace error.append("Invalid role selected.")
content = content.replace(
    'errors.append("Invalid role selected.")',
    'errors.append(gettext("Invalid role selected."))'
)

# Replace error.append("Invalid phone number.")
content = content.replace(
    'errors.append("Invalid phone number.")',
    'errors.append(gettext("Invalid phone number."))'
)

with open('/workspace/routes/users/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed error messages in routes.py")
