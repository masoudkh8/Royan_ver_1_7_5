import os
import sys
import subprocess

# TODO: Translate -  Path File‌ها
po_file = "translations/fa/LC_MESSAGES/messages.po"
mo_file = "translations/fa/LC_MESSAGES/messages.mo"

def compile_po_to_mo(po_path, mo_path):
    """
    کامپایل فایل PO به MO با استفاده از کتابخانه استاندارد پایتون (بدون نیاز به نصب gettext روی سیستم)
    این تابع از ماژول داخلی babel برای کامپایل استفاده می‌کند اگر موجود باشد،
    در غیر این صورت از پیاده‌سازی خالص پایتون استفاده می‌کند.
    """
    if not os.path.exists(po_path):
        print(f"❌ فایل {po_path} یافت نشد.")
        return False

    try:
        # TODO: Translate -  Create پوشه مقصد اگر وجود نداReject
        os.makedirs(os.path.dirname(mo_path), exist_ok=True)

        # TODO: Translate -  تلاش برای استفاده از babel اگر نصب باشد
        try:
            from babel.messages import pofile, mofile
            # TODO: Translate -  استفاده از babel برای کامپایل
            catalog = pofile.read_po(open(po_path, 'rb'))
            mo_data = mofile.write_mo(catalog)
            with open(mo_path, 'wb') as f:
                f.write(mo_data)
            
            if os.path.exists(mo_path) and os.path.getsize(mo_path) > 0:
                print(f"✅ فایل MO با موفقیت ساخته شد (با Babel): {mo_path}")
                return True
        except ImportError:
            pass  # TODO: Translate -  اگر babel نصب نبود، از روش جایگزین استفاده می‌کنیم
        except Exception as babel_error:
            print(f"⚠️ خطا در Babel: {babel_error}، استفاده از روش جایگزین...")

        # TODO: Translate -  روش جایگزین: Read File PO و Write باینری MO به صورت دستی
        # TODO: Translate -  این یک پیاده‌سازی ساده‌شده است
        import struct
        import hashlib
        
        translations = {}
        current_msgid = None
        current_msgstr = ""
        in_msgstr = False
        
        with open(po_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('msgid'):
                    if current_msgid is not None:
                        translations[current_msgid] = current_msgstr
                    current_msgid = line[6:].strip().strip('"')[1:-1] if len(line) > 7 else ""
                    current_msgstr = ""
                    in_msgstr = False
                elif line.startswith('msgstr'):
                    in_msgstr = True
                    current_msgstr = line[7:].strip().strip('"')[1:-1] if len(line) > 8 else ""
                elif in_msgstr and line.startswith('"') and line.endswith('"'):
                    current_msgstr += line[1:-1]
                elif line == '' or line.startswith('#'):
                    continue
        
        if current_msgid is not None:
            translations[current_msgid] = current_msgstr
        
        # TODO: Translate -  Write File MO به فرمت باینری ساده
        # TODO: Translate -  هدر File MO
        magic = 0x950412de  # TODO: Translate -  جادویی برای File‌های MO
        revision = 0
        num_strings = len(translations)
        
        # TODO: Translate -  محاسبه آفست‌ها
        header_size = 28  # TODO: Translate -  اندازه هدر ثابت
        key_table_offset = header_size
        value_table_offset = key_table_offset + (num_strings * 8)
        
        keys_data = []
        values_data = []
        current_offset = value_table_offset
        
        key_offsets = []
        value_offsets = []
        
        for key, value in sorted(translations.items()):
            if not key:  # TODO: Translate -  Key خالی را Reject کن
                continue
            
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            
            keys_data.append(key_bytes)
            values_data.append(value_bytes)
            
            key_offsets.append((len(key_bytes), current_offset))
            current_offset += len(key_bytes)
            
            value_offsets.append((len(value_bytes), current_offset))
            current_offset += len(value_bytes)
        
        # TODO: Translate -  ساخت باینری
        binary_data = struct.pack('<I', magic)  # TODO: Translate -  جادویی
        binary_data += struct.pack('<I', revision)  # TODO: Translate -  نسخه
        binary_data += struct.pack('<I', num_strings)  # TODO: Translate -  تعداد String‌ها
        binary_data += struct.pack('<I', key_table_offset)  # TODO: Translate -  آفست Table Keyها
        binary_data += struct.pack('<I', value_table_offset)  # TODO: Translate -  آفست Table مقادیر
        binary_data += struct.pack('<I', 0)  # TODO: Translate -  اندازه Table هش (0 برای ساده)
        binary_data += struct.pack('<I', 0)  # TODO: Translate -  آفست Table هش
        
        # TODO: Translate -  Table Keyها (طول، آفست)
        for length, offset in key_offsets:
            binary_data += struct.pack('<I', length)
            binary_data += struct.pack('<I', offset)
        
        # TODO: Translate -  Table مقادیر (طول، آفست)
        for length, offset in value_offsets:
            binary_data += struct.pack('<I', length)
            binary_data += struct.pack('<I', offset)
        
        # TODO: Translate -  Data‌های Keyها
        for key_bytes in keys_data:
            binary_data += key_bytes
        
        # TODO: Translate -  Data‌های مقادیر
        for value_bytes in values_data:
            binary_data += value_bytes
        
        with open(mo_path, 'wb') as f:
            f.write(binary_data)
        
        if os.path.exists(mo_path) and os.path.getsize(mo_path) > 0:
            print(f"✅ فایل MO با موفقیت ساخته شد (روش خالص پایتون): {mo_path}")
            return True
        else:
            print("❌ فایل MO ساخته نشد یا خالی است.")
            return False
            
    except Exception as e:
        print(f"❌ خطا در هنگام کامپایل: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🔄 در حال کامپایل {po_file} به {mo_file}...")
    success = compile_po_to_mo(po_file, mo_file)
    if not success:
        sys.exit(1)
