# models/notification.py
from . import db
from datetime import datetime
import pytz
tehran_tz = pytz.timezone('Asia/Tehran')

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # کسی که اعلان رو دریافت می‌کند
    message = db.Column(db.String(200), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))

    # رابطه
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification for {self.user.username}: {self.message[:30]}...>"