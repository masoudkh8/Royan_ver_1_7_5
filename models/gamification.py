# models/gamification.py
"""
بخش ۳: سیستم اعتبار و گیمیفیکیشن حرفه‌ای (Trust & Gamification)
- موتور امتیازدهی پویا
- نشان‌های افتخار (Badges)
- چالش‌های فصلی
- پیشرفت شخصی
"""
from . import db
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')


class UserBadge(db.Model):
    """نشان‌های افتخار کاربران"""
    __tablename__ = 'user_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)  # e.g., 'export_expert', 'top_seller'
    badge_name = db.Column(db.String(100), nullable=False)  # e.g., 'متخصص صادرات به عمان'
    badge_icon = db.Column(db.String(20))  # emoji or icon name
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    description = db.Column(db.Text)
    
    # رابطه
    user = db.relationship('User', back_populates='badges')


class UserProgress(db.Model):
    """داشبورد پیشرفت شخصی کاربران"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # امتیاز کل گیمیفیکیشن
    total_points = db.Column(db.Integer, default=0)
    
    # سطح کاربر (Level)
    level = db.Column(db.Integer, default=1)
    
    # پیشرفت به سطح بعدی (۰-۱۰۰ درصد)
    progress_to_next_level = db.Column(db.Integer, default=0)
    
    # آمار فعالیت‌ها
    completed_profile = db.Column(db.Boolean, default=False)
    successful_trades = db.Column(db.Integer, default=0)
    content_created = db.Column(db.Integer, default=0)  # تعداد محتوای مفید
    referrals = db.Column(db.Integer, default=0)  # تعداد معرفی‌های موفق
    
    # آخرین فعالیت
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    # رابطه
    user = db.relationship('User', back_populates='progress')
    
    def calculate_level(self):
        """محاسبه سطح بر اساس امتیاز کل"""
        # فرمول ساده: هر ۱۰۰۰ امتیاز = ۱ سطح
        self.level = (self.total_points // 1000) + 1
        return self.level
    
    def get_next_actions(self):
        """پیشنهاد ۳ اقدام بعدی برای ارتقا"""
        actions = []
        if not self.completed_profile:
            actions.append("تکمیل پروفایل شرکتی (+۲۰۰ امتیاز)")
        if self.successful_trades is None or self.successful_trades < 5:
            actions.append("انجام اولین معامله موفق (+۵۰۰ امتیاز)")
        if self.content_created is None or self.content_created < 3:
            actions.append("اشتراک‌گذاری محتوای تخصصی (+۱۰۰ امتیاز)")
        if self.referrals is None or self.referrals < 2:
            actions.append("معرفی همکار تجاری (+۱۵۰ امتیاز)")
        return actions[:3]


class SeasonalChallenge(db.Model):
    """چالش‌های فصلی با پاداش‌های ملموس"""
    __tablename__ = 'seasonal_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    reward_type = db.Column(db.String(50))  # e.g., 'discount', 'priority', 'credit'
    reward_value = db.Column(db.String(100))  # e.g., '20% off logistics'
    is_active = db.Column(db.Boolean, default=True)
    
    # شرکت‌کنندگان
    participants = db.relationship('ChallengeParticipant', back_populates='challenge', cascade='all, delete-orphan')


class ChallengeParticipant(db.Model):
    """شرکت‌کنندگان در چالش‌های فصلی"""
    __tablename__ = 'challenge_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('seasonal_challenges.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)  # درصد پیشرفت
    completed = db.Column(db.Boolean, default=False)
    reward_claimed = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    # روابط
    challenge = db.relationship('SeasonalChallenge', back_populates='participants')
    user = db.relationship('User', backref='challenge_participations')
