#!/usr/bin/env python3
"""
Extract Persian to English translations from various files and create a PO file
"""

import re
import os
from collections import OrderedDict

def extract_from_persian_to_english_translation(filepath):
    """Extract from persian_to_english_translation.txt format: Persian -> English"""
    translations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '->' in line and not line.startswith('#') and not line.startswith('='):
                parts = line.split('->')
                if len(parts) == 2:
                    persian = parts[0].strip().strip('"\'')
                    english = parts[1].strip().strip('"\'')
                    if persian and english and len(persian) > 1:
                        translations.append((persian, english))
    return translations

def extract_from_translations_txt(filepath):
    """Extract from translations.txt format: "Persian" → "English" or Persian → English"""
    translations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '→' in line or '->' in line:
                # Handle different arrow types
                separator = '→' if '→' in line else '->'
                parts = line.split(separator)
                if len(parts) == 2:
                    persian = parts[0].strip().strip('"\'').strip('-').strip()
                    english = parts[1].strip().strip('"\'')
                    if persian and english and len(persian) > 1 and not persian.startswith('#'):
                        translations.append((persian, english))
    return translations

def extract_from_dictionary_md(filepath):
    """Extract from TRANSLATION_DICTIONARY.md format: Persian | English | context"""
    translations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '|' in line and not line.startswith('#'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    persian = parts[0].strip()
                    english = parts[1].strip()
                    if persian and english and len(persian) > 1:
                        translations.append((persian, english))
    return translations

def extract_from_markdown_table(filepath):
    """Extract from markdown tables in translations_list.md and persian_translations.md"""
    translations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find table rows with Persian | English pattern
    lines = content.split('\n')
    for line in lines:
        if '|' in line and not line.startswith('#') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2:
                # Check if first column looks like Persian (has Persian characters)
                first = parts[0].strip()
                second = parts[1].strip() if len(parts) > 1 else ''
                if any('\u0600' <= c <= '\u06FF' for c in first) and second:
                    if len(first) > 1 and not first.startswith('#'):
                        translations.append((first, second))
    return translations

def create_po_file(translations, output_path):
    """Create a proper PO file from translations"""
    
    # Remove duplicates while preserving order
    seen = set()
    unique_translations = []
    for persian, english in translations:
        key = (persian, english)
        if key not in seen:
            seen.add(key)
            unique_translations.append((persian, english))
    
    # Sort by Persian text for better organization
    unique_translations.sort(key=lambda x: x[0])
    
    po_content = '''# Metisma Platform - Persian to English Translation Dictionary
# Copyright (C) 2024 Metisma
# This file is distributed under the same license as the Metisma project.
#
msgid ""
msgstr ""
"Project-Id-Version: Metisma Platform 1.0\\n"
"Report-Msgid-Bugs-To: support@metisma.com\\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"PO-Revision-Date: 2024-01-01 00:00+0330\\n"
"Last-Translator: Metisma Team\\n"
"Language: en\\n"
"Language-Team: Persian to English\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: Metisma Translation Extractor\\n"

'''
    
    for persian, english in unique_translations:
        # Escape special characters for PO format
        persian_escaped = persian.replace('\\', '\\\\').replace('"', '\\"')
        english_escaped = english.replace('\\', '\\\\').replace('"', '\\"')
        
        po_content += f'msgid "{persian_escaped}"\n'
        po_content += f'msgstr "{english_escaped}"\n\n'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(po_content)
    
    return len(unique_translations)

def main():
    all_translations = []
    
    # Files to process
    files_config = [
        ('/workspace/persian_to_english_translation.txt', extract_from_persian_to_english_translation),
        ('/workspace/translations_persian_to_english.txt', extract_from_translations_txt),
        ('/workspace/persian_to_english_translations.txt', extract_from_translations_txt),
        ('/workspace/persian_to_english_translations_batch2.txt', extract_from_translations_txt),
        ('/workspace/translations.txt', extract_from_translations_txt),
        ('/workspace/translations_dashboard.txt', extract_from_translations_txt),
        ('/workspace/translations_edit_role_perms.txt', extract_from_translations_txt),
        ('/workspace/translations_log.txt', extract_from_translations_txt),
        ('/workspace/docs/TRANSLATION_DICTIONARY.md', extract_from_dictionary_md),
        ('/workspace/translations_list.md', extract_from_markdown_table),
        ('/workspace/persian_translations.md', extract_from_markdown_table),
    ]
    
    print("Extracting translations from files...")
    for filepath, extractor in files_config:
        if os.path.exists(filepath):
            translations = extractor(filepath)
            print(f"  ✓ {filepath}: {len(translations)} translations")
            all_translations.extend(translations)
        else:
            print(f"  ✗ {filepath}: File not found")
    
    print(f"\nTotal translations extracted: {len(all_translations)}")
    
    # Create PO file
    output_file = '/workspace/translations_complete.po'
    count = create_po_file(all_translations, output_file)
    
    print(f"\n✓ Created PO file: {output_file}")
    print(f"  Total unique translations: {count}")

if __name__ == '__main__':
    main()
