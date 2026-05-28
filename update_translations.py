#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
استخراج تمام متن‌های انگلیسی از پروژه و به‌روزرسانی فایل PO برای ترجمه
"""
import re
import os
from datetime import datetime

def extract_texts_from_html(filepath):
    """TODO: Translate - استخراج متن‌های قابل مشاهده از File HTML"""
    texts = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # TODO: Translate -  استخراج متن بین تگ‌ها (بدون Variableهای Jinja2)
    pattern = r'>([^<>{}%]+?)<'
    matches = re.findall(pattern, content)
    
    for match in matches:
        text = match.strip()
        if (len(text) > 1 and 
            len(text) < 300 and
            not text.startswith('{') and 
            not text.endswith('}') and
            not text.startswith('%') and
            not text.endswith('%') and
            not text.replace(' ', '').replace('-', '').isdigit()):
            texts.append(text)
    
    return texts

def extract_flash_messages(filepath):
    """TODO: Translate - استخراج Message‌های flash از File Python"""
    messages = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # TODO: Translate -  پیدا کRejectن تمام flash() ها
    patterns = [
        r'flash\([\'"]([^\'"]+)[\'"]',
        r"flash\([\"']([^\"']+)[\"']",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match.strip():
                messages.append(match.strip())
    
    return messages

def extract_all_texts(workspace):
    """TODO: Translate - استخراج تمام متن‌ها از پروژه"""
    all_texts = {}
    
    # TODO: Translate -  استخراج از تمپلیت‌ها
    templates_dir = os.path.join(workspace, 'templates')
    print("=== در حال استخراج متن از تمپلیت‌ها ===")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, workspace)
                texts = extract_texts_from_html(filepath)
                if texts:
                    if rel_path not in all_texts:
                        all_texts[rel_path] = []
                    all_texts[rel_path].extend(texts)
                    print(f"  ✓ {rel_path}: {len(texts)} متن")
    
    # TODO: Translate -  استخراج Message‌های flash از routes
    routes_dir = os.path.join(workspace, 'routes')
    print("\n=== در حال استخراج پیام‌های flash از routeها ===")
    flash_messages = {}
    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, workspace)
                messages = extract_flash_messages(filepath)
                if messages:
                    if rel_path not in flash_messages:
                        flash_messages[rel_path] = []
                    flash_messages[rel_path].extend(messages)
                    print(f"  ✓ {rel_path}: {len(messages)} پیام")
    
    # TODO: Translate -  استخراج از app.py
    app_file = os.path.join(workspace, 'app.py')
    if os.path.exists(app_file):
        messages = extract_flash_messages(app_file)
        if messages:
            flash_messages['app.py'] = messages
            print(f"  ✓ app.py: {len(messages)} پیام")
    
    return all_texts, flash_messages

def update_po_file(po_file, all_texts, flash_messages):
    """TODO: Translate - Update File PO با متن‌های جدید"""
    
    # TODO: Translate -  Read File PO فعلی
    existing_msgids = set()
    if os.path.exists(po_file):
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # TODO: Translate -  پیدا کRejectن تمام msgidهای موجود
            pattern = r'^msgid "(.*?)"$'
            matches = re.findall(pattern, content, re.MULTILINE)
            existing_msgids = set(matches)
    
    # TODO: Translate -  جمع‌آوری تمام متن‌های یکتا
    all_unique_texts = set()
    for filepath, texts in all_texts.items():
        all_unique_texts.update(texts)
    
    for filepath, messages in flash_messages.items():
        all_unique_texts.update(messages)
    
    print(f"\n=== آمار ===")
    print(f"متن‌های موجود در PO: {len(existing_msgids)}")
    print(f"متن‌های کل استخراج شده: {len(all_unique_texts)}")
    
    # TODO: Translate -  پیدا کRejectن متن‌های جدید
    new_texts = all_unique_texts - existing_msgids
    print(f"متن‌های جدید نیازمند ترجمه: {len(new_texts)}")
    
    if new_texts:
        print(f"\n=== افزودن {len(new_texts)} متن جدید به فایل PO ===")
        
        with open(po_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# Added on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for text in sorted(new_texts):
                # TODO: Translate -  فرار دادن کاراکترهای خاص
                escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
                f.write(f'\n#: templates/\nmsgid "{escaped_text}"\n')
                f.write('msgstr ""\n')
        
        print("✓ متن‌های جدید با موفقیت اضافه شدند")
    else:
        print("✓ هیچ متن جدیدی یافت نشد")
    
    return len(new_texts)

def main():
    workspace = '/workspace'
    po_file = os.path.join(workspace, 'translations', 'fa', 'LC_MESSAGES', 'messages.po')
    
    print("🔍 شروع استخراج متن‌ها از پروژه...\n")
    
    # TODO: Translate -  استخراج تمام متن‌ها
    all_texts, flash_messages = extract_all_texts(workspace)
    
    #  Update File PO
    new_count = update_po_file(po_file, all_texts, flash_messages)
    
    print(f"\n✅ فرآیند تکمیل شد!")
    print(f"   {new_count} متن جدید به فایل PO اضافه شد")
    print(f"   فایل: {po_file}")
    print("\n📝 حالا می‌توانید:")
    print("   1. فایل PO را ویرایش کنید و ترجمه‌ها را وارد کنید")
    print("   2. دستور زیر را اجرا کنید تا فایل MO ساخته شود:")
    print("      msgfmt -o translations/fa/LC_MESSAGES/messages.mo translations/fa/LC_MESSAGES/messages.po")

if __name__ == '__main__':
    main()
