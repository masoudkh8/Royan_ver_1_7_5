# models/user.py
# from flask_sqlalchemy import SQLAlchemy
from . import db
from flask_login import UserMixin
from enum import Enum
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')


class Role(Enum):
    """8 تخصصی نقش‌های کاربری بر اساس CONTEXT_MASTER_BRIEF"""
    PRODUCER = 'producer'              # تولیدکننده/صادرکننده
    BUYER = 'buyer'                    # واردکننده/خریدار
    BROKER = 'broker'                  # کارگزار تجاری
    CORPORATE_AGENT = 'corporate_agent' # نماینده شرکتی
    LOGISTICS = 'logistics'            # خدمات لجستیک و بیمه
    LEGAL = 'legal'                    # خدمات حقوقی و انطباق
    TECH_PARTNER = 'tech_partner'      # شریک فناوری
    INVESTOR = 'investor'              # سرمایه‌گذار مالی
    ADMIN = 'admin'                    # مدیریت سیستم
    MODERATOR = 'moderator'            # ناظر محتوا
    
    @staticmethod
    def has_value(value):
        return value in [role.value for role in Role]
    
    @staticmethod
    def get_display_name(role_value):
        """دریافت نام نمایشی فارسی نقش"""
        display_names = {
            'producer': 'تولیدکننده/صادرکننده',
            'buyer': 'واردکننده/خریدار',
            'broker': 'کارگزار تجاری',
            'corporate_agent': 'نماینده شرکتی',
            'logistics': 'خدمات لجستیک و بیمه',
            'legal': 'خدمات حقوقی و انطباق',
            'tech_partner': 'شریک فناوری',
            'investor': 'سرمایه‌گذار مالی',
            'admin': 'مدیر سیستم',
            'moderator': 'ناظر محتوا'
        }
        return display_names.get(role_value, role_value)
    
    @staticmethod
    def get_core_roles():
        """دریافت نقش‌های اصلی تجاری (بدون Admin و Moderator)"""
        return [role.value for role in Role if role.value not in ['admin', 'moderator']]


class UserProfile(db.Model):
    """پروفایل تخصصی کاربران با فیلدهای مخصوص هر نقش"""
    __tablename__ = 'user_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # اطلاعات عمومی پروفایل
    bio = db.Column(db.Text)  # بیوگرافی حرفه‌ای
    website = db.Column(db.String(200))
    linkedin = db.Column(db.String(200))
    telegram = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    
    # فیلدهای تخصصی بر اساس نقش
    # برای Producer/Exporter
    production_capacity = db.Column(db.String(100))  # ظرفیت تولید
    export_experience_years = db.Column(db.Integer)  # سال‌های سابقه صادرات
    main_products = db.Column(db.Text)  # محصولات اصلی
    certifications = db.Column(db.Text)  # گواهینامه‌ها (ISO, HACCP, etc.)
    target_markets = db.Column(db.Text)  # بازارهای هدف
    
    # برای Buyer/Importer
    annual_import_volume = db.Column(db.String(100))  # حجم واردات سالانه
    main_categories = db.Column(db.Text)  # دسته‌بندی‌های اصلی مورد نیاز
    preferred_payment_terms = db.Column(db.String(200))  # شرایط پرداخت مورد علاقه
    
    # برای Broker
    specialization_sectors = db.Column(db.Text)  # بخش‌های تخصصی
    broker_license_number = db.Column(db.String(50))  # شماره پروانه کارگزاری
    commission_rate = db.Column(db.String(20))  # نرخ کمیسیون
    
    # برای Corporate Agent
    company_position = db.Column(db.String(100))  # سمت در شرکت
    authorization_level = db.Column(db.String(100))  # سطح اختیارات
    # parent_company_id commented out until Company model is created
    # parent_company_id = db.Column(db.Integer, db.ForeignKey('company.id'))  # شرکت مادر
    
    # برای Logistics & Insurance
    service_types = db.Column(db.Text)  # انواع خدمات (حمل دریایی، هوایی، زمینی، بیمه)
    coverage_regions = db.Column(db.Text)  # مناطق تحت پوشش
    insurance_license = db.Column(db.String(50))  # مجوز بیمه
    fleet_size = db.Column(db.String(50))  # اندازه ناوگان
    
    # برای Legal & Compliance
    practice_areas = db.Column(db.Text)  # حوزه‌های فعالیت (گمرک، قراردادها، داوری)
    bar_association_number = db.Column(db.String(50))  # شماره کانون وکلا
    years_of_practice = db.Column(db.Integer)  # سال‌های فعالیت
    
    # برای Tech Partner
    tech_specialties = db.Column(db.Text)  # تخصص‌های فنی (ERP, CRM, AI, Blockchain)
    portfolio_url = db.Column(db.String(200))  # لینک نمونه کارها
    service_packages = db.Column(db.Text)  # بسته‌های خدماتی
    
    # برای Investor
    investment_capacity = db.Column(db.String(100))  # ظرفیت سرمایه‌گذاری
    preferred_sectors = db.Column(db.Text)  # بخش‌های مورد علاقه برای سرمایه‌گذاری
    investment_type = db.Column(db.String(100))  # نوع سرمایه‌گذاری (VC, Angel, Project-based)
    risk_tolerance = db.Column(db.String(50))  # سطح ریسک‌پذیری
    
    # وضعیت‌ها
    is_verified = db.Column(db.Boolean, default=False)  # تأیید هویت انجام شده
    verification_date = db.Column(db.DateTime)
    is_premium = db.Column(db.Boolean, default=False)
    premium_since = db.Column(db.DateTime)
    trust_score_override = db.Column(db.Integer)  # امتیاز اعتماد دستی (برای Admin)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='profile')
    # company relationship will be established when Company model is created
    # documents and endorsements can be added as separate models if needed


# جدول واسط برای اتصالات (Follow System) - باید قبل از کلاس User تعریف شود
connections = db.Table('connections',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now()),
    db.Column('connection_type', db.String(20), default='follow') # follow, connect, partner
)


class MembershipTier(Enum):
    """لایه‌های دسترسی باشگاه نخبگان (Concentric Circles Model)"""
    OBSERVER = 'observer'          # لایه ۱: بازدیدکننده (تازه وارد،未احراز)
    VERIFIED = 'verified'          # لایه ۲: عضو تأیید شده (KYC تکمیل، حق عضویت پایه)
    PARTNER = 'partner'            # لایه ۳: شریک استراتژیک (TrustScore > 70، دعوت یا عملکرد بالا)
    ELITE = 'elite'                # لایه ۴: نخبگان (دعوت اختصاصی، TrustScore > 90، تایید هیئت مدیره)
    
    @staticmethod
    def get_display_name(tier_value):
        """دریافت نام نمایشی فارسی لایه"""
        display_names = {
            'observer': 'بازدیدکننده',
            'verified': 'عضو تأیید شده',
            'partner': 'شریک استراتژیک',
            'elite': 'نخبه'
        }
        return display_names.get(tier_value, tier_value)
    
    @staticmethod
    def get_hierarchy_level(tier_value):
        """دریافت سطح سلسله مراتبی برای مقایسه"""
        hierarchy = {
            'observer': 0,
            'verified': 1,
            'partner': 2,
            'elite': 3
        }
        return hierarchy.get(tier_value, 0)


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)

    # === سیستم لایه‌بندی باشگاه نخبگان ===
    membership_tier = db.Column(db.Enum(MembershipTier), default=MembershipTier.OBSERVER, nullable=False, index=True)
    
    # سیستم دعوت‌نامه (انحصار ورود)
    invite_code = db.Column(db.String(32), unique=True, index=True, nullable=True)  # کد دعوت خود کاربر
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # چه کسی دعوت کرده؟
    invited_by = db.relationship('User', remote_side=[id], backref='invitees', foreign_keys=[invited_by_id])
    
    # امتیاز اعتماد (کلید ارتقای لایه)
    trust_score_value = db.Column(db.Integer, default=50, nullable=False, index=True)  # ✅ امتیاز اولیه 50
    
    # وضعیت احراز هویت (شرط ورود به لایه ۲)
    is_kyc_verified = db.Column(db.Boolean, default=False, nullable=False)
    kyc_documents_url = db.Column(db.String(255), nullable=True)
    
    # === فیلدهای تخصصی پروفایل (درخواست ۱) ===
    expertise_area = db.Column(db.String(200))  # حوزه تخصصی برای متخصصین
    job_title = db.Column(db.String(100))  # عنوان شغلی
    bio = db.Column(db.Text)  # درباره من / بیوگرافی حرفه‌ای
    website = db.Column(db.String(200))  # وبسایت شخصی/شرکتی
    social_links = db.Column(db.Text)  # لینک‌های اجتماعی (JSON format)
    
    # وضعیت تأیید هویت (درخواست ۱)
    is_verified = db.Column(db.Boolean, default=False)  # ✅ تأیید هویت انجام شده
    verification_documents = db.Column(db.Text)  # مدارک تأیید هویت (JSON format)
    
    # === فیلدهای امنیتی و احراز هویت ===
    # Avatar/Profile Picture
    avatar_filename = db.Column(db.String(255), nullable=True)  # نام فایل عکس پروفایل
    
    # Two-Factor Authentication (2FA)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)  # رمز的秘密 برای TOTP
    backup_codes = db.Column(db.Text, nullable=True)  # کدهای پشتیبان (JSON format)
    
    # Account Lockout
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)  # زمان قفل بودن حساب
    
    # Password History (برای جلوگیری از استفاده مجدد)
    password_history = db.Column(db.Text, nullable=True)  # JSON array of previous password hashes
    
    # Email Verification
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    
    # Dark Mode Preference (stored in backend)
    dark_mode_preference = db.Column(db.String(20), default='system', nullable=False)  # 'light', 'dark', 'system'
    
    # Notification Preferences (JSON)
    notification_preferences = db.Column(db.Text, nullable=True)  # JSON settings for notifications
    
    # Privacy Settings (JSON)
    privacy_settings = db.Column(db.Text, nullable=True)  # JSON settings for privacy
    
    # تاریخچه
    last_login = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    notifications = db.relationship('Notification', 
                                   foreign_keys='Notification.user_id',
                                   back_populates='user', 
                                   lazy='dynamic',
                                   cascade='all, delete-orphan')

    company_name = db.Column(db.String(100))
    country = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)  # ✅ فعال/غیرفعال
    is_premium = db.Column(db.Boolean, default=False)
    premium_since = db.Column(db.DateTime, default=None)
    premium_requests = db.relationship('PremiumRequest', back_populates='user', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # New relationships for 16-section platform
    profile = db.relationship('UserProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    trust_score = db.relationship('TrustScore', back_populates='user', uselist=False, cascade='all, delete-orphan')
    badges = db.relationship('UserBadge', back_populates='user', cascade='all, delete-orphan')
    progress = db.relationship('UserProgress', back_populates='user', uselist=False, cascade='all, delete-orphan')
    credit_account = db.relationship('TradeCreditAccount', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    # روابط اجتماعی (Follow System) - استفاده از مدل Follow از social.py
    # relationshipهای follow/followers در models/social.py به User اضافه می‌شوند
    # اینجا فقط برای سازگاری با کدهای قدیمی تعریف شده
    
    # پست‌ها - relationship در models/social.py تعریف شده است
    # برای جلوگیری از تداخل، اینجا تعریف نمی‌کنیم

  
    @property
    def unread_notifications_count(self):
        return self.notifications.filter_by(user_id=self.id, is_read=False).count()
    
    @property
    def role_display_name(self):
        """دریافت نام نمایشی فارسی نقش کاربر"""
        return Role.get_display_name(self.role.value) if self.role else None
    
    @property
    def tier_display_name(self):
        """دریافت نام نمایشی فارسی لایه عضویت"""
        return MembershipTier.get_display_name(self.membership_tier.value) if self.membership_tier else 'بازدیدکننده'
    
    @property
    def is_core_member(self):
        """آیا کاربر جزو اعضای اصلی باشگاه نخبگان است؟"""
        return self.role.value in Role.get_core_roles() if self.role else False
    
    @property
    def is_admin_or_moderator(self):
        """آیا کاربر دسترسی مدیریتی دارد؟"""
        return self.role.value in ['admin', 'moderator'] if self.role else False
    
    def can_access_tier(self, required_tier: MembershipTier) -> bool:
        """بررسی دسترسی هوشمند بر اساس لایه باشگاه"""
        if not self.membership_tier or not required_tier:
            return False
        return MembershipTier.get_hierarchy_level(self.membership_tier.value) >= MembershipTier.get_hierarchy_level(required_tier.value)
    
    def generate_invite_code(self):
        """تولید کد دعوت منحصر به فرد"""
        import secrets
        if not self.invite_code:
            self.invite_code = f"{self.username.upper()[:4]}-{secrets.token_hex(4)}"
        return self.invite_code
    
    def follow(self, user):
        """دنبال کردن کاربر دیگر"""
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        """آنفالو کردن کاربر"""
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        """آیا این کاربر، کاربر دیگر را دنبال می‌کند؟"""
        return self.followed.filter(
            connections.c.followed_id == user.id).count() > 0
    
    def get_public_profile_url(self):
        """دریافت لینک پروفایل عمومی"""
        return f"/user/{self.username}"
    
    def to_dict(self):
        """تبدیل به دیکشنری برای API"""
        import json
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'role_display': self.role_display_name,
            'tier': self.membership_tier.value if self.membership_tier else 'observer',
            'tier_display': self.tier_display_name,
            'trust_score': self.trust_score_value,
            'is_verified': self.is_verified or self.is_kyc_verified,
            'company_name': self.company_name,
            'country': self.country,
            'invite_code': self.invite_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # فیلدهای تخصصی جدید
            'expertise_area': self.expertise_area,
            'job_title': self.job_title,
            'bio': self.bio,
            'website': self.website,
            'social_links': json.loads(self.social_links) if self.social_links else {},
            'verification_documents': json.loads(self.verification_documents) if self.verification_documents else []
        }
    
    def set_password(self, password):
        """تنظیم رمز عبور با هش کردن"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """بررسی رمز عبور"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role.value}) [{self.membership_tier.value}]>"
