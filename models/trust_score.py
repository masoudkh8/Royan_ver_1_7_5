# models/trust_score.py
"""
بخش ۷: لایه اعتماد چندبعدی (Trust Stack)
- امتیاز اعتبار پویا برای هر کاربر
- لایه‌های تأیید هویت، تخصص، اعتبار اجتماعی
"""
from . import db
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')


class TrustScore(db.Model):
    __tablename__ = 'trust_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # TODO: Translate -  لایه ۱: Confirm هویت پایه (۰-۲۵ Score)
    identity_verified = db.Column(db.Boolean, default=False)  # TODO: Translate -  مدارک ثبت شرکت
    identity_score = db.Column(db.Integer, default=0)  # 0-25
    
    # TODO: Translate -  لایه ۲: Confirm تخصصی (۰-۲۵ Score)
    expertise_verified = db.Column(db.Boolean, default=False)  # TODO: Translate -  گواهی Product، سابقه صادرات
    expertise_score = db.Column(db.Integer, default=0)  # 0-25
    
    # TODO: Translate -  لایه ۳: Credit اجتماعی (۰-۲۵ Score)
    social_score = db.Column(db.Integer, default=0)  # TODO: Translate -  0-25 (Commentات، معاملات Success)
    
    # TODO: Translate -  لایه ۴: Credit پویا (۰-۲۵ Score)
    dynamic_score = db.Column(db.Integer, default=0)  # TODO: Translate -  0-25 (سرعت Responseگویی، دقت تحویل)
    
    # TODO: Translate -  Score کل (۰-۱۰۰)
    total_score = db.Column(db.Integer, default=0)
    
    # TODO: Translate -  Dateچه تغییرات
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz), onupdate=lambda: datetime.now(tehran_tz))
    
    #  Relationship
    user = db.relationship('User', back_populates='trust_score')
    
    def calculate_total(self):
        """TODO: Translate - محاسبه خودکار Score کل"""
        self.total_score = self.identity_score + self.expertise_score + self.social_score + self.dynamic_score
        return self.total_score
    
    def get_badge(self):
        """TODO: Translate - دریافت نشان Credit بر اساس Score"""
        score = self.total_score or 0
        if score >= 90:
            return "Platinum 🏆"
        elif score >= 75:
            return "Gold 🥇"
        elif score >= 50:
            return "Silver 🥈"
        elif score >= 25:
            return "Bronze 🥉"
        else:
            return "Newcomer 🆕"
