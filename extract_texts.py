#!/usr/bin/env python
"""
استخراج تمام متن‌های انگلیسی از فایل‌های HTML و Python برای ترجمه
"""
import os
import re
from pathlib import Path

def extract_text_from_html(html_file):
    """TODO: Translate - استخراج متن‌های قابل مشاهده از File HTML"""
    texts = []
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # TODO: Translate -  استخراج متن بین تگ‌ها
    pattern = r'>([^<>\n{}]+?)<'
    matches = re.findall(pattern, content)
    
    for match in matches:
        text = match.strip()
        # TODO: Translate -  فیلتر کRejectن متن‌های کوتاه، Variableها و کدها
        if (len(text) > 2 and 
            not text.startswith('{') and 
            not text.endswith('}') and
            not text.startswith('%') and
            not text.endswith('%') and
            not text.isdigit() and
            len(text) < 200):
            texts.append(text)
    
    return texts

def extract_flash_messages(py_file):
    """TODO: Translate - استخراج Message‌های flash از File‌های Python"""
    messages = []
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # TODO: Translate -  پیدا کRejectن تمام flash() ها
    pattern = r'flash\([\'"]([^\'"]+)[\'"]'
    matches = re.findall(pattern, content)
    
    for match in matches:
        if match.strip() and not match.startswith('{'):
            messages.append(match.strip())
    
    return messages

def main():
    workspace = '/workspace'
    templates_dir = os.path.join(workspace, 'templates')
    routes_dir = os.path.join(workspace, 'routes')
    
    all_texts = {}
    
    # TODO: Translate -  استخراج از تمپلیت‌ها
    print("=== استخراج متن از تمپلیت‌ها ===\n")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, workspace)
                texts = extract_text_from_html(filepath)
                if texts:
                    all_texts[rel_path] = texts
                    print(f"\n{rel_path}:")
                    for text in texts[:10]:  # TODO: Translate -  View ۱۰ تای اول
                        print(f"  - {text}")
                    if len(texts) > 10:
                        print(f"  ... و {len(texts) - 10} متن دیگر")
    
    # TODO: Translate -  استخراج Message‌های flash
    print("\n\n=== استخراج پیام‌های flash از routeها ===\n")
    flash_messages = []
    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, workspace)
                messages = extract_flash_messages(filepath)
                if messages:
                    flash_messages.extend(messages)
                    print(f"\n{rel_path}:")
                    for msg in messages[:5]:
                        print(f"  - {msg}")
    
    # TODO: Translate -  Save در File
    output_file = os.path.join(workspace, 'texts_to_translate.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("متن‌های استخراج شده برای ترجمه به فارسی\n")
        f.write("=" * 50 + "\n\n")
        
        for filepath, texts in all_texts.items():
            f.write(f"\n### {filepath} ###\n")
            for text in texts:
                f.write(f"{text}\n")
        
        f.write("\n\n# TODO: Translate - ## Message‌های Flash ###\n")
        for msg in set(flash_messages):
            f.write(f"{msg}\n")
    
    print(f"\n\n✅ تمام متن‌ها در فایل {output_file} ذخیره شدند.")

if __name__ == '__main__':
    main()
