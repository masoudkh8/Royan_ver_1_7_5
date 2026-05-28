# models/consortium.py
"""
بخش ۵: ماژول کنسرسیوم‌سازی هوشمند (Consortium Engine)
- موتور کشف فرصت‌های کنسرسیومی
- سیستم پیشنهاد شریک هوشمند
- پنل مدیریت کنسرسیوم
- قرارداد هوشمند
"""
from . import db
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')


class ConsortiumProject(db.Model):
    """TODO: Translate - پروژه‌های بزرگ نیازمند مشارکت چند شرکت"""
    __tablename__ = 'consortium_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # TODO: Translate -  Information پروژه
    industry = db.Column(db.String(100))  # TODO: Translate -  صنعت مرتبط
    target_country = db.Column(db.String(100))  # TODO: Translate -  کشور هدف
    required_capacity = db.Column(db.String(200))  # TODO: Translate -  ظرفیت موReject نیاز
    estimated_value = db.Column(db.String(100))  # TODO: Translate -  ارزش تقریبی
    
    #  Status
    status = db.Column(db.String(20), default='open')  # open, forming, active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    # TODO: Translate -  اعضا
    members = db.relationship('ConsortiumMember', back_populates='project', cascade='all, delete-orphan')
    
    # TODO: Translate -  قراRejectاد
    contract = db.relationship('ConsortiumContract', back_populates='project', uselist=False, cascade='all, delete-orphan')


class ConsortiumMember(db.Model):
    """TODO: Translate - اعضای هر کنسرسیوم"""
    __tablename__ = 'consortium_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('consortium_projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # TODO: Translate -  Role در کنسرسیوم
    role = db.Column(db.String(50), nullable=False)  # e.g., 'leader', 'supplier', 'logistics_partner'
    
    # TODO: Translate -  سهم سرمایه (درصد)
    capital_share = db.Column(db.Integer, default=0)  # 0-100
    
    # TODO: Translate -  سهم سود (درصد)
    profit_share = db.Column(db.Integer, default=0)  # 0-100
    
    #  Status
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    status = db.Column(db.String(20), default='active')  # active, left, removed
    
    # TODO: Translate -  روابط
    project = db.relationship('ConsortiumProject', back_populates='members')
    user = db.relationship('User', backref='consortium_memberships')


class ConsortiumContract(db.Model):
    """TODO: Translate - قراRejectاد هوشمند کنسرسیوم"""
    __tablename__ = 'consortium_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('consortium_projects.id'), unique=True, nullable=False)
    
    # TODO: Translate -  مفاد قراRejectاد
    terms = db.Column(db.Text)  # TODO: Translate -  شرایط و ضوابط
    responsibilities = db.Column(db.Text)  # TODO: Translate -  مسئولیت‌های هر عضو
    
    # TODO: Translate -  توزیع سود
    profit_distribution_method = db.Column(db.String(100))  # e.g., 'proportional_to_capital'
    
    # TODO: Translate -  شرایط Logout
    exit_conditions = db.Column(db.Text)
    
    # TODO: Translate -  امضاها
    signed_by = db.Column(db.Text)  # TODO: Translate -  List Userانی که امضا کRejectه‌اند (JSON)
    fully_signed = db.Column(db.Boolean, default=False)
    
    #  Time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    #  Relationship
    project = db.relationship('ConsortiumProject', back_populates='contract')


class PartnerMatch(db.Model):
    """TODO: Translate - پیشنهادات شریک هوشمند"""
    __tablename__ = 'partner_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # TODO: Translate -  Userان برای تطبیق
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # TODO: Translate -  Score تطابق (۰-۱۰۰)
    match_score = db.Column(db.Integer, default=0)
    
    # TODO: Translate -  دلیل تطابق
    match_reasons = db.Column(db.Text)  # TODO: Translate -  e.g., 'مکمل در صنعت X', 'تجربه در کشور Y'
    
    #  Status
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    # TODO: Translate -  روابط
    user1 = db.relationship('User', foreign_keys=[user1_id], backref='partner_matches_as_user1')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='partner_matches_as_user2')
