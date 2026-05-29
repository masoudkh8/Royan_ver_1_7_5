#!/usr/bin/env python3
"""
Script to add translation tags to HTML templates.
This script will:
1. Find all text content in HTML templates that should be translated
2. Wrap them with _() or t_() function calls
3. Handle both {{ }} and {% %} blocks
"""

import os
import re
from pathlib import Path

# Text patterns that should NOT be translated
SKIP_PATTERNS = [
    r'^\s*$',  # Empty lines
    r'^[\d\s\-\_\.\,\:\;\!\?\(\)\[\]\{\}\<\>\@\#\$\%\^\&\*\+\=\/\\\|]+$',  # Only symbols/numbers
    r'^[a-z0-9\._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',  # Email patterns
    r'^https?://',  # URLs
    r'^/{{',  # Jinja variables
    r'^{%',  # Jinja tags
    r'^{{\s*\w+',  # Already a variable
    r't_\(',  # Already translated
    r'_\(',  # Already translated
    r'gettext\(',  # Already translated
    r'^fa-',  # Font Awesome classes
    r'^bg-',  # Bootstrap classes
    r'^text-',  # Bootstrap classes
    r'^flex',  # CSS classes
    r'^grid',  # CSS classes
    r'^w-',  # Width classes
    r'^h-',  # Height classes
    r'^p-',  # Padding classes
    r'^m-',  # Margin classes
    r'^rounded',  # Border radius classes
    r'^shadow',  # Shadow classes
    r'^border',  # Border classes
    r'^hover:',  # Hover states
    r'^focus:',  # Focus states
    r'^dark:',  # Dark mode classes
    r'^md:',  # Medium breakpoint
    r'^lg:',  # Large breakpoint
    r'^xl:',  # Extra large breakpoint
    r'^2xl:',  # 2XL breakpoint
    r'^sm:',  # Small breakpoint
    r'^max-w',  # Max width
    r'^min-h',  # Min height
]

def should_skip(text):
    """Check if text should be skipped for translation."""
    text = text.strip()
    if len(text) < 2:
        return True
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False

def extract_text_from_html(content):
    """Extract text nodes from HTML that need translation."""
    # Pattern to match text between tags (not inside {{ }} or {% %})
    # This is a simplified approach - we'll look for text in specific contexts
    
    texts_to_translate = []
    
    # Match text in HTML elements (simplified)
    # Looking for patterns like: >Text< or >Text </tag>
    pattern = r'>([^<{}]+?)<'
    
    for match in re.finditer(pattern, content):
        text = match.group(1).strip()
        if text and not should_skip(text):
            texts_to_translate.append((match.start(), match.end(), text))
    
    return texts_to_translate

def wrap_text_with_translation(content, texts_to_translate):
    """Wrap extracted texts with translation function."""
    # Sort by position in reverse order to avoid offset issues
    texts_to_translate.sort(key=lambda x: x[0], reverse=True)
    
    new_content = content
    for start, end, text in texts_to_translate:
        # Find the actual positions in the current content
        escaped_text = re.escape(text.strip())
        pattern = f'>{escaped_text}<'
        
        match = re.search(pattern, new_content)
        if match:
            # Replace with translated version
            replacement = f'>{{{{ _("{text.strip()}") }}}}'
            new_content = new_content[:match.start()] + replacement + new_content[match.end():]
    
    return new_content

def process_html_file(filepath):
    """Process a single HTML file."""
    print(f"Processing: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Extract texts that need translation
    texts = extract_text_from_html(content)
    
    if not texts:
        print(f"  No texts to translate in {filepath}")
        return False
    
    print(f"  Found {len(texts)} texts to translate")
    
    # For now, let's use a simpler approach - just identify common patterns
    # and wrap them manually with more context-aware logic
    
    return True

def simple_wrap_translations(filepath):
    """Simple approach: wrap common text patterns in templates."""
    print(f"Processing with simple approach: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    original_content = content
    
    # Common patterns to translate in HTML templates
    # Pattern 1: Text in labels
    content = re.sub(
        r'<label[^>]*>([^<{}]+?)</label>',
        lambda m: f'<label{m.group(0)[7:-8]}>{{{{ _("{m.group(1).strip()}") }}}}</label>' if not '_(' in m.group(0) else m.group(0),
        content
    )
    
    # Pattern 2: Text in buttons (simple ones)
    content = re.sub(
        r'<button[^>]*>([^<{}]+?)</button>',
        lambda m: m.group(0) if '_(' in m.group(0) or '{{' in m.group(0) else f'<button{m.group(0)[8:-9]}>{{{{ _("{m.group(1).strip()}") }}}}</button>',
        content
    )
    
    # Pattern 3: Text in links
    content = re.sub(
        r'<a[^>]*>([^<{}]+?)</a>',
        lambda m: m.group(0) if '_(' in m.group(0) or '{{' in m.group(0) else f'<a{m.group(0)[2:-4]}>{{{{ _("{m.group(1).strip()}") }}}}</a>',
        content
    )
    
    # Pattern 4: Text in headings
    for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        content = re.sub(
            f'<{tag}[^>]*>([^<{{}}]+?)</{tag}>',
            lambda m, t=tag: m.group(0) if '_(' in m.group(0) or '{{' in m.group(0) else f'<{t}{m.group(0)[len(t)+2:-len(t)-4]}>{{{{ _("{m.group(1).strip()}") }}}}</{t}>',
            content
        )
    
    # Pattern 5: Title attributes
    content = re.sub(
        r'title="([^"]+?)"',
        lambda m: m.group(0) if '_(' in m.group(0) else f'title="{{{{ _(\"{m.group(1)}\") }}}}"',
        content
    )
    
    # Pattern 6: Placeholder attributes
    content = re.sub(
        r'placeholder="([^"]+?)"',
        lambda m: m.group(0) if '_(' in m.group(0) else f'placeholder="{{{{ _(\"{m.group(1)}\") }}}}"',
        content
    )
    
    # Pattern 7: Alt attributes
    content = re.sub(
        r'alt="([^"]+?)"',
        lambda m: m.group(0) if '_(' in m.group(0) else f'alt="{{{{ _(\"{m.group(1)}\") }}}}"',
        content
    )
    
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Updated {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    print(f"  No changes needed for {filepath}")
    return False

def main():
    templates_dir = Path('/workspace/templates')
    
    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        return
    
    html_files = list(templates_dir.rglob('*.html'))
    print(f"Found {len(html_files)} HTML files to process\n")
    
    updated_count = 0
    for html_file in html_files:
        if simple_wrap_translations(str(html_file)):
            updated_count += 1
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Total files: {len(html_files)}")
    print(f"Updated files: {updated_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
