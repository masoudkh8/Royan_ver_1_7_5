# models/trade_credit.py
"""
بخش ۶: سیستم اعتبار تجاری درون‌پلتفرمی (TradeCredit System)
- واحد اعتباری داخلی (غیرارزی)
- موتور کسب و مصرف اعتبار
- گزارش‌گیری تاریخچه اعتبار
"""
from . import db
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')


class TradeCreditAccount(db.Model):
    """TODO: Translate - Account Credit تجاری هر User"""
    __tablename__ = 'trade_credit_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # TODO: Translate -  موجودی Credit (واحد: تِRejectکُReject - TC)
    balance = db.Column(db.Integer, default=0)
    
    # TODO: Translate -  Credit رزرو شده (برای معاملات در جریان)
    reserved_balance = db.Column(db.Integer, default=0)
    
    # TODO: Translate -  Dateچه
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    last_transaction_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    #  Relationship
    user = db.relationship('User', back_populates='credit_account')
    
    def get_available_balance(self):
        """TODO: Translate - محاسبه موجودی قابل استفاده"""
        balance = self.balance or 0
        reserved = self.reserved_balance or 0
        return balance - reserved
    
    def add_credit(self, amount, reason, transaction_type='earn'):
        """TODO: Translate - افزایش Credit"""
        if amount > 0:
            self.balance += amount
            self.last_transaction_at = datetime.now(tehran_tz)
            
            # TODO: Translate -  ثبت Transaction
            transaction = CreditTransaction(
                user_id=self.user_id,
                amount=amount,
                transaction_type=transaction_type,
                reason=reason,
                balance_after=self.balance
            )
            db.session.add(transaction)
            return True
        return False
    
    def spend_credit(self, amount, reason, transaction_type='spend'):
        """TODO: Translate - مصرف Credit"""
        available = self.get_available_balance()
        if amount > 0 and amount <= available:
            self.balance -= amount
            self.last_transaction_at = datetime.now(tehran_tz)
            
            # TODO: Translate -  ثبت Transaction
            transaction = CreditTransaction(
                user_id=self.user_id,
                amount=-amount,
                transaction_type=transaction_type,
                reason=reason,
                balance_after=self.balance
            )
            db.session.add(transaction)
            return True
        return False
    
    def reserve_credit(self, amount):
        """TODO: Translate - رزرو Credit برای معامله"""
        available = self.get_available_balance()
        if amount > 0 and amount <= available:
            self.reserved_balance += amount
            return True
        return False
    
    def release_reservation(self, amount):
        """TODO: Translate - آزادسازی Credit رزرو شده"""
        if amount > 0 and amount <= self.reserved_balance:
            self.reserved_balance -= amount
            return True
        return False


class CreditTransaction(db.Model):
    """TODO: Translate - Dateچه Transaction‌های Creditی"""
    __tablename__ = 'credit_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # TODO: Translate -  Value تغییر (مثبت برای کسب، منفی برای مصرف)
    amount = db.Column(db.Integer, nullable=False)
    
    #  Type Transaction
    transaction_type = db.Column(db.String(20), nullable=False)  # earn, spend, reserve, release
    
    # TODO: Translate -  دلیل Transaction
    reason = db.Column(db.String(200), nullable=False)  # TODO: Translate -  e.g., 'تکمیل پروFile', 'Payment هزینه مشاوره'
    
    # TODO: Translate -  موجودی پس از Transaction
    balance_after = db.Column(db.Integer, nullable=False)
    
    # TODO: Translate -  مرجع (Optional)
    reference_id = db.Column(db.String(100))  # e.g., order_id, challenge_id
    
    #  Time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tehran_tz))
    
    #  Relationship
    user = db.relationship('User', backref='credit_transactions')


class CreditRule(db.Model):
    """TODO: Translate - قوانین کسب و مصرف Credit"""
    __tablename__ = 'credit_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'profile_completion'
    credit_amount = db.Column(db.Integer, nullable=False)  #  Value Credit
    description = db.Column(db.Text)  # TODO: Translate -  توضیح قانون
    is_active = db.Column(db.Boolean, default=True)
    
    @staticmethod
    def get_earning_rules():
        """TODO: Translate - دریافت قوانین کسب Credit Active"""
        return CreditRule.query.filter_by(is_active=True).filter(CreditRule.credit_amount > 0).all()
    
    @staticmethod
    def get_spending_rules():
        """TODO: Translate - دریافت قوانین مصرف Credit Active"""
        return CreditRule.query.filter_by(is_active=True).filter(CreditRule.credit_amount < 0).all()
