import gettext
import os
import json

class Translator:
    def __init__(self, lang='fa'):
        self.lang = lang
        self.translations = {}
        self.translator = None
        self.load_translations()
    
    def load_translations(self):
        """بارگذاری فایل ترجمه"""
        # بارگذاری ترجمه‌های JSON (برای سازگاری با عقب)
        translations_path = os.path.join(os.path.dirname(__file__), '..', 'translations', f'{self.lang}.json')
        try:
            with open(translations_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            self.translations = {}
        
        # بارگذاری ترجمه‌های gettext (.mo فایل)
        translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
        try:
            self.translator = gettext.translation('messages', localedir=translations_dir, languages=[self.lang])
        except FileNotFoundError:
            print(f"⚠️ فایل ترجمه برای زبان {self.lang} یافت نشد. از ترجمه پیش‌فرض استفاده می‌شود.")
            self.translator = None
    
    def get(self, key, default=None):
        """دریافت ترجمه با کلید تودرتو (مثلاً 'common.login')"""
        keys = key.split('.')
        value = self.translations
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default if default else key
        return value
    
    def gettext(self, message):
        """ترجمه متن با استفاده از gettext"""
        if self.translator:
            return self.translator.gettext(message)
        return message
    
    def t(self, key, **kwargs):
        """ترجمه کلید و جایگزینی متغیرها"""
        # اول سعی کن از gettext استفاده کنی (برای متن‌های مستقیم)
        text = self.gettext(key)
        
        # اگر ترجمه‌ای پیدا نشد، از JSON استفاده کن
        if text == key:
            text = self.get(key)
        
        if kwargs:
            for k, v in kwargs.items():
                text = text.replace(f'{{{k}}}', str(v))
        return text

# نمونه جهانی
translator = Translator('fa')

def t(key, **kwargs):
    """تابع کمکی برای استفاده در تمپلیت‌ها"""
    return translator.t(key, **kwargs)
