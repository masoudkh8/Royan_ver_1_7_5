# models/user.py
# from flask_sqlalchemy import SQLAlchemy
from . import db
from flask_login import UserMixin
from enum import Enum
from datetime import datetime
import pytz
import json

tehran_tz = pytz.timezone('Asia/Tehran')


class Role(Enum):
    """8 specialized user roles based on CONTEXT_MASTER_BRIEF"""
    PRODUCER = 'producer'              # Producer/Exporter
    BUYER = 'buyer'                    # Importer/Buyer
    BROKER = 'broker'                  # Trade Broker
    CORPORATE_AGENT = 'corporate_agent' # Corporate Agent
    LOGISTICS = 'logistics'            # Logistics & Insurance Services
    LEGAL = 'legal'                    # Legal & Compliance Services
    TECH_PARTNER = 'tech_partner'      # Tech Partner
    INVESTOR = 'investor'              # Financial Investor
    ADMIN = 'admin'                    # System Administration
    MODERATOR = 'moderator'            # Content Moderator
    
    @staticmethod
    def has_value(value):
        return value in [role.value for role in Role]
    
    @staticmethod
    def get_display_name(role_value):
        """Get Persian display name for role"""
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
        """Get core business roles (excluding Admin and Moderator)"""
        return [role.value for role in Role if role.value not in ['admin', 'moderator']]


class UserProfile(db.Model):
    """TODO: Translate - پروFile تخصصی Userان با Fieldهای مخصوص هر Role"""
    __tablename__ = 'user_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # TODO: Translate -  Information عمومی پروFile
    bio = db.Column(db.Text)  # TODO: Translate -  Professional biography
    website = db.Column(db.String(200))
    linkedin = db.Column(db.String(200))
    telegram = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    
    # TODO: Translate -  Fieldهای تخصصی بر اساس Role
    # TODO: Translate -  برای Producer/Exporter
    production_capacity = db.Column(db.String(100))  # TODO: Translate -  Production capacity
    export_experience_years = db.Column(db.Integer)  # TODO: Translate -  Years of export experience
    main_products = db.Column(db.Text)  # TODO: Translate -  Productات اصلی
    certifications = db.Column(db.Text)  # TODO: Translate -  Certifications (ISO, HACCP, etc.)
    target_markets = db.Column(db.Text)  # TODO: Translate -  Target markets
    
    # TODO: Translate -  برای Buyer/Importer
    annual_import_volume = db.Column(db.String(100))  # TODO: Translate -  حجم واRejectات سالانه
    main_categories = db.Column(db.Text)  # TODO: Translate -  دسته‌بندی‌های اصلی موReject نیاز
    preferred_payment_terms = db.Column(db.String(200))  # TODO: Translate -  شرایط Payment موReject علاقه
    
    # TODO: Translate -  برای Broker
    specialization_sectors = db.Column(db.Text)  # TODO: Translate -  Section‌های تخصصی
    broker_license_number = db.Column(db.String(50))  # TODO: Translate -  Broker license number
    commission_rate = db.Column(db.String(20))  # TODO: Translate -  Commission rate
    
    # TODO: Translate -  برای Corporate Agent
    company_position = db.Column(db.String(100))  # TODO: Translate -  Company position
    authorization_level = db.Column(db.String(100))  # TODO: Translate -  Authorization level
    # parent_company_id commented out until Company model is created
    # TODO: Translate -  parent_company_id = db.Column(db.Integer, db.ForeignKey('company.id'))  # شرکت مادر
    
    # TODO: Translate -  برای Logistics & Insurance
    service_types = db.Column(db.Text)  # TODO: Translate -  Service types (حمل دریایی، هوایی، زمینی، بیمه)
    coverage_regions = db.Column(db.Text)  # TODO: Translate -  Coverage regions
    insurance_license = db.Column(db.String(50))  # TODO: Translate -  Permission بیمه
    fleet_size = db.Column(db.String(50))  # TODO: Translate -  Fleet size
    
    # TODO: Translate -  برای Legal & Compliance
    practice_areas = db.Column(db.Text)  # TODO: Translate -  حوزه‌های Activeیت (گمرک، قرارDataا، داوری)
    bar_association_number = db.Column(db.String(50))  # TODO: Translate -  Bar association number
    years_of_practice = db.Column(db.Integer)  # TODO: Translate -  سال‌های Activeیت
    
    # TODO: Translate -  برای Tech Partner
    tech_specialties = db.Column(db.Text)  # TODO: Translate -  Technical specialties (ERP, CRM, AI, Blockchain)
    portfolio_url = db.Column(db.String(200))  # TODO: Translate -  Portfolio URL
    service_packages = db.Column(db.Text)  # TODO: Translate -  Service packages
    
    # TODO: Translate -  برای Investor
    investment_capacity = db.Column(db.String(100))  # TODO: Translate -  Investment capacity
    preferred_sectors = db.Column(db.Text)  # TODO: Translate -  Section‌های موReject علاقه برای سرمایه‌گذاری
    investment_type = db.Column(db.String(100))  # TODO: Translate -  Type سرمایه‌گذاری (VC, Angel, Project-based)
    risk_tolerance = db.Column(db.String(50))  # TODO: Translate -  Risk tolerance
    
    # TODO: Translate -  Status‌ها
    is_verified = db.Column(db.Boolean, default=False)  # TODO: Translate -  Confirm هویت انجام شده
    verification_date = db.Column(db.DateTime)
    is_premium = db.Column(db.Boolean, default=False)
    premium_since = db.Column(db.DateTime)
    trust_score_override = db.Column(db.Integer)  # TODO: Translate -  Score Trust دستی (برای Admin)
    
    # TODO: Translate -  === System Permissionهای Orderی (Custom Permissions) ===
    # TODO: Translate -  این Field اجازه می‌دهد Access‌های User را به صورت ریزدانه تنظیم کنید
    # TODO: Translate -  اگر NULL یا خالی باشد، از Permissionهای Default Role استفاده می‌شود
    # TODO: Translate -  فرمت: JSON Array از String‌های Permission (مثلاً ["order.view", "logistics.update_status"])
    custom_permissions = db.Column(db.Text, nullable=True)  # JSON format
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='profile')
    # company relationship will be established when Company model is created
    # documents and endorsements can be added as separate models if needed
    
    def get_custom_permissions(self):
        """
        Get custom permissions list as list of strings
        Returns empty list if profile doesn't exist or custom_permissions is empty
        """
        if not self.custom_permissions:
            return []
        try:
            if isinstance(self.custom_permissions, str):
                perms = json.loads(self.custom_permissions)
                return perms if isinstance(perms, list) else []
            elif isinstance(self.custom_permissions, list):
                return self.custom_permissions
            else:
                return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_custom_permissions(self, permissions_list):
        """
        Set custom permissions as list of permission value strings
        Args:
            permissions_list: لیستی از رشته‌ها مانند ['order.view', 'logistics.update_status']
        """
        if not permissions_list or len(permissions_list) == 0:
            self.custom_permissions = None
        else:
            # TODO: Translate -  اطمینان از اینکه فقط String‌های معتبر Save شوند
            valid_perms = [str(p) for p in permissions_list if p]
            self.custom_permissions = json.dumps(valid_perms, ensure_ascii=False)
    
    def add_permission(self, permission_value):
        """
        Add a permission to custom permissions
        Args:
            permission_value: رشته مجوز مانند 'order.view'
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_perms = self.get_custom_permissions()
            if permission_value not in current_perms:
                current_perms.append(permission_value)
                self.set_custom_permissions(current_perms)
                return True
            return False
        except Exception:
            return False
    
    def remove_permission(self, permission_value):
        """
        Remove a permission from custom permissions
        Args:
            permission_value: رشته مجوز مانند 'order.view'
        Returns:
            bool: True if permission was removed, False if it didn't exist
        """
        try:
            current_perms = self.get_custom_permissions()
            if permission_value in current_perms:
                current_perms.remove(permission_value)
                self.set_custom_permissions(current_perms)
                return True
            return False
        except Exception:
            return False
    
    def has_permission(self, permission_value):
        """
        Check if a permission exists in custom permissions
        Args:
            permission_value: رشته مجوز مانند 'order.view'
        Returns:
            bool: True if permission exists
        """
        return permission_value in self.get_custom_permissions()


# TODO: Translate -  Table واسط برای اتصالات (Follow System) - باید قبل از Class User تعریف شود
connections = db.Table('connections',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=db.func.now()),
    db.Column('connection_type', db.String(20), default='follow') # follow, connect, partner
)


class MembershipTier(Enum):
    """TODO: Translate - لایه‌های Access باشگاه نخبگان (Concentric Circles Model)"""
    OBSERVER = 'observer'          # TODO: Translate -  لایه ۱: Observer (تازه واReject،未احراز)
    VERIFIED = 'verified'          # TODO: Translate -  لایه ۲: عضو Confirm شده (KYC تکمیل، حق عضویت پایه)
    PARTNER = 'partner'            # TODO: Translate -  لایه ۳: Strategic Partner (TrustScore > 70، دعوت یا عملکReject بالا)
    ELITE = 'elite'                # TODO: Translate -  لایه ۴: نخبگان (دعوت اختصاصی، TrustScore > 90، تایید هیئت مدیره)
    
    @staticmethod
    def get_display_name(tier_value):
        """TODO: Translate - دریافت نام Viewی فارسی لایه"""
        display_names = {
            'observer': 'Observer',
            'verified': 'Verified Member',
            'partner': 'Strategic Partner',
            'elite': 'Elite'
        }
        return display_names.get(tier_value, tier_value)
    
    @staticmethod
    def get_hierarchy_level(tier_value):
        """TODO: Translate - Get hierarchy level for comparison"""
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

    # TODO: Translate -  === System لایه‌بندی باشگاه نخبگان ===
    membership_tier = db.Column(db.Enum(MembershipTier), default=MembershipTier.OBSERVER, nullable=False, index=True)
    
    # TODO: Translate -  System دعوت‌نامه (انحصار Login)
    invite_code = db.Column(db.String(32), unique=True, index=True, nullable=True)  # TODO: Translate -  کد دعوت خود User
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # TODO: Translate -  چه کسی دعوت کRejectه؟
    invited_by = db.relationship('User', remote_side=[id], backref='invitees', foreign_keys=[invited_by_id])
    
    # TODO: Translate -  Score Trust (Key ارتقای لایه)
    trust_score_value = db.Column(db.Integer, default=50, nullable=False, index=True)  # TODO: Translate -  ✅ Score اولیه 50
    
    # TODO: Translate -  Status Authentication (شرط Login به لایه ۲)
    is_kyc_verified = db.Column(db.Boolean, default=False, nullable=False)
    kyc_documents_url = db.Column(db.String(255), nullable=True)
    
    # TODO: Translate -  === Fieldهای تخصصی پروFile (Request ۱) ===
    expertise_area = db.Column(db.String(200))  # TODO: Translate -  حوزه تخصصی برای متخصصین
    job_title = db.Column(db.String(100))  # TODO: Translate -  عنوان شغلی
    bio = db.Column(db.Text)  # TODO: Translate -  درباره من / Professional biography
    website = db.Column(db.String(200))  # TODO: Translate -  وبسایت شخصی/شرکتی
    social_links = db.Column(db.Text)  # TODO: Translate -  لینک‌های اجتماعی (JSON format)
    
    # TODO: Translate -  Status Confirm هویت (Request ۱)
    is_verified = db.Column(db.Boolean, default=False)  # TODO: Translate -  ✅ Confirm هویت انجام شده
    verification_documents = db.Column(db.Text)  # TODO: Translate -  مدارک Confirm هویت (JSON format)
    
    # TODO: Translate -  === Fieldهای امنیتی و Authentication ===
    # Avatar/Profile Picture
    avatar_filename = db.Column(db.String(255), nullable=True)  # TODO: Translate -  نام File عکس پروFile
    
    # Two-Factor Authentication (2FA)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)  # TODO: Translate -  رمز的秘密 برای TOTP
    backup_codes = db.Column(db.Text, nullable=True)  # TODO: Translate -  کدهای پشتیبان (JSON format)
    
    # Account Lockout
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)  # TODO: Translate -  Time قفل بودن Account
    
    # TODO: Translate -  Password History (برای جلوگیری از استفاده مجدد)
    password_history = db.Column(db.Text, nullable=True)  # JSON array of previous password hashes
    
    # Email Verification
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True)

    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ===================================




    # Dark Mode Preference (stored in backend)
    dark_mode_preference = db.Column(db.String(20), default='system', nullable=False)  # 'light', 'dark', 'system'
    
    # Notification Preferences (JSON)
    notification_preferences = db.Column(db.Text, nullable=True)  # JSON settings for notifications
    
    # Privacy Settings (JSON)
    privacy_settings = db.Column(db.Text, nullable=True)  # JSON settings for privacy
    
    # TODO: Translate -  Dateچه
    last_login = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    notifications = db.relationship('Notification', 
                                   foreign_keys='Notification.user_id',
                                   back_populates='user', 
                                   lazy='dynamic',
                                   cascade='all, delete-orphan')

    company_name = db.Column(db.String(100))
    country = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)  # TODO: Translate -  ✅ Active/غیرActive
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
    
    # TODO: Translate -  روابط اجتماعی (Follow System) - استفاده از Model Follow از social.py
    # TODO: Translate -  relationshipهای follow/followers در models/social.py به User اضافه می‌شوند
    # TODO: Translate -  اینجا فقط برای سازگاری با کدهای قدیمی تعریف شده
    
    # TODO: Translate -  Post‌ها - relationship در models/social.py تعریف شده است
    # TODO: Translate -  برای جلوگیری از تداخل، اینجا تعریف نمی‌کنیم

  
    @property
    def unread_notifications_count(self):
        return self.notifications.filter_by(user_id=self.id, is_read=False).count()
    
    @property
    def role_display_name(self):
        """TODO: Translate - دریافت نام Viewی فارسی Role User"""
        return Role.get_display_name(self.role.value) if self.role else None
    
    @property
    def tier_display_name(self):
        """TODO: Translate - دریافت نام Viewی فارسی لایه عضویت"""
        return MembershipTier.get_display_name(self.membership_tier.value) if self.membership_tier else 'Observer'
    
    @property
    def is_core_member(self):
        """TODO: Translate - آیا User جزو اعضای اصلی باشگاه نخبگان است؟"""
        return self.role.value in Role.get_core_roles() if self.role else False
    
    @property
    def is_admin_or_moderator(self):
        """TODO: Translate - آیا User Access مدیریتی داReject؟"""
        return self.role.value in ['admin', 'moderator'] if self.role else False
    
    def can_access_tier(self, required_tier: MembershipTier) -> bool:
        """TODO: Translate - Check Access هوشمند بر اساس لایه باشگاه"""
        if not self.membership_tier or not required_tier:
            return False
        return MembershipTier.get_hierarchy_level(self.membership_tier.value) >= MembershipTier.get_hierarchy_level(required_tier.value)
    
    def generate_invite_code(self):
        """TODO: Translate - تولید کد دعوت منحصر به فReject"""
        import secrets
        if not self.invite_code:
            self.invite_code = f"{self.username.upper()[:4]}-{secrets.token_hex(4)}"
        return self.invite_code
    
    def follow(self, user):
        """TODO: Translate - Follow User دیگر"""
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        """TODO: Translate - آنفالو کRejectن User"""
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        """TODO: Translate - آیا این User، User دیگر را دنبال می‌کند؟"""
        return self.followed.filter(
            connections.c.followed_id == user.id).count() > 0
    
    def get_public_profile_url(self):
        """TODO: Translate - دریافت لینک پروFile عمومی"""
        return f"/user/{self.username}"
    
    def to_dict(self):
        """TODO: Translate - تبدیل به Dictionary برای API"""
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
            # TODO: Translate -  Fieldهای تخصصی جدید
            'expertise_area': self.expertise_area,
            'job_title': self.job_title,
            'bio': self.bio,
            'website': self.website,
            'social_links': json.loads(self.social_links) if self.social_links else {},
            'verification_documents': json.loads(self.verification_documents) if self.verification_documents else []
        }
    
    def set_password(self, password):
        """TODO: Translate - تنظیم Password با هش کRejectن"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check Password"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role.value}) [{self.membership_tier.value}]>"
