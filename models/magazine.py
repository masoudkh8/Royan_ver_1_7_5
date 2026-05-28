# models/magazine.py

from . import db
from datetime import datetime
import pytz
tehran_tz = pytz.timezone('Asia/Tehran')


class Magazine(db.Model):
    """TODO: Translate - Model Information کلی مجله"""
    __tablename__ = 'magazines'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='Imazhe magazine')
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    is_active = db.Column(db.Boolean, default=True)
    
    # TODO: Translate -  Relationship با شماره‌های مجله
    issues = db.relationship('MagazineIssue', backref='magazine', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Magazine {self.title}>'


class MagazineIssue(db.Model):
    """TODO: Translate - Model شماره‌های مجله"""
    __tablename__ = 'magazine_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    magazine_id = db.Column(db.Integer, db.ForeignKey('magazines.id'), nullable=False)
    issue_number = db.Column(db.Integer, nullable=False)  # TODO: Translate -  شماره نشریه
    title = db.Column(db.String(200), nullable=False)  # TODO: Translate -  عنوان شماره
    description = db.Column(db.Text)  # TODO: Translate -  توضیحات شماره
    cover_image_url = db.Column(db.String(500))  # TODO: Translate -  URL تصویر جلد
    file_url = db.Column(db.String(500), nullable=False)  # TODO: Translate -  URL File PDF برای Download
    file_size = db.Column(db.String(50))  # TODO: Translate -  حجم File
    publish_date = db.Column(db.Date, nullable=False)  # TODO: Translate -  Date انتشار
    is_published = db.Column(db.Boolean, default=False)  # TODO: Translate -  Status انتشار
    download_count = db.Column(db.Integer, default=0)  # TODO: Translate -  تعداد Download
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    
    def __repr__(self):
        return f'<MagazineIssue {self.issue_number} - {self.title}>'


class SponsorshipRequest(db.Model):
    """TODO: Translate - Model Request اسپانسری"""
    __tablename__ = 'sponsorship_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # TODO: Translate -  اگر User لاگین کRejectه باشد
    full_name = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))  # TODO: Translate -  نام شرکت
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)  # TODO: Translate -  Message و توضیحات
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    
    # TODO: Translate -  Relationship با User
    user = db.relationship('User', backref=db.backref('sponsorship_requests', lazy=True))
    
    def __repr__(self):
        return f'<SponsorshipRequest {self.email}>'


class AdvertisementRequest(db.Model):
    """TODO: Translate - Model Request تبلیغات در مجله"""
    __tablename__ = 'advertisement_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    full_name = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    ad_type = db.Column(db.String(50))  # TODO: Translate -  Type تبلیغ: full_page, half_page, quarter_page, etc.
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    
    # TODO: Translate -  Relationship با User
    user = db.relationship('User', backref=db.backref('advertisement_requests', lazy=True))
    
    def __repr__(self):
        return f'<AdvertisementRequest {self.email}>'


class Subscription(db.Model):
    """TODO: Translate - Model اشتراک سالیانه مجله"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)  # TODO: Translate -  آدرس Postی برای ارسال نسخه چاپی
    subscription_type = db.Column(db.String(50), default='annual')  # annual, semi_annual
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=False)
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    price = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    
    # TODO: Translate -  Relationship با User
    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))
    
    def __repr__(self):
        return f'<Subscription {self.email}>'
