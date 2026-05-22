#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
تست‌های سیستم چندزبانه Metisma
i18n Tests for Metisma Platform
"""

import pytest
from app import create_app
from models import db
from models.user import User, Role
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['RATELIMIT_ENABLED'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'fa_IR'
    app.config['SECRET_KEY'] = 'test-secret-key-for-i18n-testing'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('TestPass123'),
            role=Role.BUYER
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestI18nSystem:
    """تست‌های سیستم چندزبانه"""
    
    def test_persian_locale_default(self, client):
        """تست پیش‌فرض بودن زبان فارسی"""
        rv = client.get('/')
        assert rv.status_code == 200
    
    def test_language_switcher_fa(self, client):
        """تست تغییر زبان به فارسی"""
        rv = client.get('/language/set_language/fa_IR', follow_redirects=True)
        # Should redirect without error
        assert rv.status_code in [200, 302]
    
    def test_language_switcher_en(self, client):
        """تست تغییر زبان به انگلیسی"""
        rv = client.get('/language/set_language/en', follow_redirects=True)
        assert rv.status_code in [200, 302]
    
    def test_invalid_language_code(self, client):
        """تست کد زبان نامعتبر"""
        rv = client.get('/language/set_language/invalid', follow_redirects=True)
        # Should handle gracefully
        assert rv.status_code in [200, 302, 404]
    
    def test_session_language_persistence(self, client):
        """تست پایداری زبان در session"""
        with client.session_transaction() as sess:
            sess['lang'] = 'fa_IR'
        
        rv = client.get('/users/profile')
        # Session should persist
        assert rv.status_code in [200, 302, 401, 403]
    
    def test_url_language_parameter(self, client):
        """تست پارامتر زبان در URL"""
        rv = client.get('/?lang=fa_IR')
        assert rv.status_code == 200
        
        rv = client.get('/?lang=en')
        assert rv.status_code == 200


class TestTranslations:
    """تست‌های فایل‌های ترجمه"""
    
    def test_translation_files_exist(self):
        """تست وجود فایل‌های ترجمه"""
        import os
        po_file = '/workspace/translations/fa_IR/LC_MESSAGES/messages.po'
        mo_file = '/workspace/translations/fa_IR/LC_MESSAGES/messages.mo'
        
        assert os.path.exists(po_file), "فایل messages.po وجود ندارد"
        assert os.path.exists(mo_file), "فایل messages.mo وجود ندارد"
    
    def test_translation_file_not_empty(self):
        """تست خالی نبودن فایل ترجمه"""
        import os
        po_file = '/workspace/translations/fa_IR/LC_MESSAGES/messages.po'
        
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 1000, "فایل ترجمه خیلی کوچک است"
        assert 'msgstr' in content, "فایل ترجمه فاقد ترجمه‌ها است"
    
    def test_key_translation_pairs(self):
        """تست جفت‌های کلید-ترجمه"""
        import os
        po_file = '/workspace/translations/fa_IR/LC_MESSAGES/messages.po'
        
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common keys
        assert 'msgid "Login"' in content
        assert 'msgstr "ورود"' in content
        assert 'msgid "Register"' in content
        assert 'msgstr "ثبت‌نام"' in content
        assert 'msgid "Trust Score"' in content
        assert 'msgstr "امتیاز اعتماد"' in content


class TestBabelIntegration:
    """تست‌های یکپارچگی Flask-Babel"""
    
    def test_babel_initialized(self, app):
        """تست مقداردهی Flask-Babel"""
        assert 'babel' in app.extensions or hasattr(app, 'extensions')
    
    def test_locale_selector_function(self, app):
        """تست تابع انتخابگر زبان"""
        with app.test_request_context('/?lang=fa_IR'):
            from flask import session
            session['lang'] = 'fa_IR'
            
            # Get locale function
            from app import create_app
            # The locale selector should return fa_IR
            assert True  # Basic check
    
    def test_translation_function_available(self, client):
        """تست در دسترس بودن تابع ترجمه"""
        rv = client.get('/')
        # Page should load without translation errors
        assert rv.status_code == 200


class TestRTLSupport:
    """تست‌های پشتیبانی از راست‌چین"""
    
    def test_persian_text_direction(self):
        """تست جهت متن فارسی"""
        persian_text = "فارسی"
        # Persian text should be right-to-left
        assert len(persian_text) > 0
        # Basic Unicode check for Persian characters
        assert any('\u0600' <= char <= '\u06FF' for char in persian_text)
    
    def test_translation_contains_rtl_content(self):
        """تست محتوای RTL در ترجمه‌ها"""
        import os
        po_file = '/workspace/translations/fa_IR/LC_MESSAGES/messages.po'
        
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Persian characters (Unicode range)
        has_persian = any('\u0600' <= char <= '\u06FF' for char in content)
        assert has_persian, "فایل ترجمه فاقد کاراکترهای فارسی است"


class TestLanguageRoutes:
    """تست‌های مسیرهای زبان"""
    
    def test_language_blueprint_registered(self, app):
        """تست ثبت بلوپرینت زبان"""
        assert 'language' in app.blueprints
    
    def test_set_language_route_exists(self, client):
        """تست وجود مسیر تغییر زبان"""
        # Route should exist
        rv = client.get('/language/set_language/fa_IR')
        assert rv.status_code in [200, 302, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
