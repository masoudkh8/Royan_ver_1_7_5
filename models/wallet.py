# models/wallet.py
# TODO: Translate -  Section ۱۰: Financial Layer - مدیریت Payment‌ها و Wallet

from . import db
from datetime import datetime
from enum import Enum
import uuid

class Currency(Enum):
    IRR = 'IRR'  # TODO: Translate -  ریال ایران
    USD = 'USD'  # TODO: Translate -  دلار آمریکا
    EUR = 'EUR'  # TODO: Translate -  یورو
    AED = 'AED'  # TODO: Translate -  درهم امارات
    TRY = 'TRY'  # TODO: Translate -  لیر ترکیه
    CNY = 'CNY'  # TODO: Translate -  یوان چین

class WalletTransactionType(Enum):
    DEPOSIT = 'deposit'  # TODO: Translate -  واریز
    WITHDRAWAL = 'withdrawal'  # TODO: Translate -  بRejectاشت
    PAYMENT = 'payment'  #  Payment
    REFUND = 'refund'  # TODO: Translate -  بازگشت وجه
    TRANSFER = 'transfer'  # TODO: Translate -  انتقال
    ESCROW_HOLD = 'escrow_hold'  # TODO: Translate -  بلوکه در Account امانی
    ESCROW_RELEASE = 'escrow_release'  # TODO: Translate -  آزادسازی از امانی
    FEE = 'fee'  # TODO: Translate -  کارمزد
    CREDIT_CONVERSION = 'credit_conversion'  # TODO: Translate -  تبدیل Credit به پول

class TransactionStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REVERSED = 'reversed'

class PaymentMethod(Enum):
    BANK_TRANSFER = 'bank_transfer'  # TODO: Translate -  انتقال بانکی
    ONLINE_GATEWAY = 'online_gateway'  # TODO: Translate -  درگاه آنلاین
    CRYPTO = 'crypto'  # TODO: Translate -  ارز دیجیتال
    CASH = 'cash'  # TODO: Translate -  نقدی
    CREDIT = 'credit'  # TODO: Translate -  Creditی

class Wallet(db.Model):
    """
    کیف پول کاربر - بخش ۱۰
    """
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    
    # TODO: Translate -  موجودی‌ها به تفکیک ارز
    balance_irr = db.Column(db.Numeric(20, 0), default=0)  # TODO: Translate -  ریال
    balance_usd = db.Column(db.Numeric(15, 2), default=0)  # TODO: Translate -  دلار
    balance_eur = db.Column(db.Numeric(15, 2), default=0)  # TODO: Translate -  یورو
    balance_aed = db.Column(db.Numeric(15, 2), default=0)  # TODO: Translate -  درهم
    
    #  Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)  # TODO: Translate -  Confirm شده برای معاملات ارزی
    
    # TODO: Translate -  محدودیت‌ها
    daily_withdrawal_limit = db.Column(db.Numeric(15, 2), default=10000)  # TODO: Translate -  سقف بRejectاشت روزانه (دلار)
    monthly_withdrawal_limit = db.Column(db.Numeric(15, 2), default=100000)  # TODO: Translate -  سقف بRejectاشت ماهانه
    
    # TODO: Translate -  آمار
    total_deposited = db.Column(db.Numeric(20, 0), default=0)  # TODO: Translate -  کل واریزی (ریال)
    total_withdrawn = db.Column(db.Numeric(20, 0), default=0)  # TODO: Translate -  کل بRejectاشتی (ریال)
    total_traded = db.Column(db.Numeric(20, 0), default=0)  # TODO: Translate -  کل معاملات
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # TODO: Translate -  روابط
    user = db.relationship('User', backref=db.backref('wallet', uselist=False))
    transactions = db.relationship('WalletTransaction', backref='wallet', lazy='dynamic', cascade='all, delete-orphan')
    escrows = db.relationship('EscrowTransaction', backref='wallet', lazy='dynamic')
    
    def get_balance(self, currency='USD'):
        """TODO: Translate - دریافت موجودی بر اساس ارز"""
        if currency == 'IRR':
            return self.balance_irr or 0
        elif currency == 'USD':
            return self.balance_usd or 0
        elif currency == 'EUR':
            return self.balance_eur or 0
        elif currency == 'AED':
            return self.balance_aed or 0
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'balances': {
                'IRR': float(self.balance_irr) if self.balance_irr else 0,
                'USD': float(self.balance_usd) if self.balance_usd else 0,
                'EUR': float(self.balance_eur) if self.balance_eur else 0,
                'AED': float(self.balance_aed) if self.balance_aed else 0,
            },
            'is_verified': self.is_verified,
            'total_traded': float(self.total_traded) if self.total_traded else 0,
        }


class WalletTransaction(db.Model):
    """
    تراکنش‌های کیف پول - بخش ۱۰
    """
    __tablename__ = 'wallet_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False, index=True)
    
    # TODO: Translate -  شناسه یکتا
    transaction_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    
    #  Type Transaction
    type = db.Column(db.Enum(WalletTransactionType), nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod))
    
    # TODO: Translate -  Amount و ارز
    amount = db.Column(db.Numeric(20, 0), nullable=False)  # TODO: Translate -  Amount اصلی
    currency = db.Column(db.Enum(Currency), nullable=False)
    
    # TODO: Translate -  Amount معادل ریالی (برای گزارش‌گیری)
    amount_irr_equivalent = db.Column(db.Numeric(20, 0))
    exchange_rate = db.Column(db.Numeric(15, 2))  # TODO: Translate -  نرخ ارز لحظه‌ای
    
    #  Status
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # TODO: Translate -  توضیحات
    description_fa = db.Column(db.Text)
    description_en = db.Column(db.Text)
    reference_number = db.Column(db.String(100))  # TODO: Translate -  شماره پیگیری
    
    #  Information Payment
    gateway_response = db.Column(db.JSON)  # TODO: Translate -  Response درگاه Payment
    bank_details = db.Column(db.JSON)  # TODO: Translate -  Information بانکی
    
    # TODO: Translate -  کارمزد
    fee_amount = db.Column(db.Numeric(15, 2), default=0)
    fee_currency = db.Column(db.String(3), default='IRR')
    
    # TODO: Translate -  Time‌بندی
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # TODO: Translate -  متادیتا اضافی
    extra_data = db.Column(db.JSON)  # TODO: Translate -  Data‌های اضافی
    
    # TODO: Translate -  روابط - Foreign Key columns
    related_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    related_escrow_id = db.Column(db.Integer, db.ForeignKey('escrow_transactions.id'), nullable=True, index=True)
    
    related_order = db.relationship('Order', backref='wallet_transaction', uselist=False)
    related_escrow = db.relationship('EscrowTransaction', backref='wallet_transaction', uselist=False)
    
    __table_args__ = (
        db.Index('idx_transaction_type', 'type'),
        db.Index('idx_transaction_status', 'status'),
        db.Index('idx_transaction_date', 'requested_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'type': self.type.value,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency.value,
            'status': self.status.value,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reference_number': self.reference_number,
        }


class EscrowTransaction(db.Model):
    """
    حساب امانی (Escrow) برای ضمانت معامله - بخش ۱۰
    """
    __tablename__ = 'escrow_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # TODO: Translate -  طرفین معامله
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False, index=True)
    
    # TODO: Translate -  مرتبط با Order
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, index=True)
    
    #  Amount
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.Enum(Currency), nullable=False)
    
    # TODO: Translate -  Status امانی
    escrow_status = db.Column(db.String(20), default='held')  # held, released, refunded, disputed
    
    # TODO: Translate -  شرایط آزادسازی
    release_conditions = db.Column(db.JSON)  # TODO: Translate -  شرایط لازم برای آزادسازی
    auto_release_date = db.Column(db.Date)  # TODO: Translate -  Date آزادسازی خودکار
    
    # TODO: Translate -  مستندات
    shipping_documents = db.Column(db.JSON)  # TODO: Translate -  اسناد حمل
    customs_documents = db.Column(db.JSON)  # TODO: Translate -  اسناد گمرکی
    inspection_report = db.Column(db.Text)  # TODO: Translate -  گزارش بازرسی
    
    # TODO: Translate -  اختلافات
    has_dispute = db.Column(db.Boolean, default=False)
    dispute_reason = db.Column(db.Text)
    dispute_resolution = db.Column(db.Text)
    
    # TODO: Translate -  Time‌بندی
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    released_at = db.Column(db.DateTime)
    
    # TODO: Translate -  روابط
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref=db.backref('escrows_as_buyer', lazy='dynamic'))
    seller = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('escrows_as_seller', lazy='dynamic'))
    order = db.relationship('Order', backref=db.backref('escrow', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency.value,
            'escrow_status': self.escrow_status,
            'has_dispute': self.has_dispute,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'released_at': self.released_at.isoformat() if self.released_at else None,
        }


class ExchangeRate(db.Model):
    """
    نرخ ارز لحظه‌ای - بخش ۱۰
    """
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    currency_from = db.Column(db.String(3), nullable=False)  # TODO: Translate -  ارز مبدا
    currency_to = db.Column(db.String(3), nullable=False)  # TODO: Translate -  ارز مقصد
    
    rate = db.Column(db.Numeric(15, 6), nullable=False)  # TODO: Translate -  نرخ تبدیل
    source = db.Column(db.String(50))  # TODO: Translate -  منبع نرخ (مثلاً: central_bank, market)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('currency_from', 'currency_to', name='unique_currency_pair'),
        db.Index('idx_currency_from', 'currency_from'),
    )
    
    @classmethod
    def get_rate(cls, from_currency, to_currency):
        """TODO: Translate - دریافت نرخ تبدیل"""
        if from_currency == to_currency:
            return 1.0
        
        rate_record = cls.query.filter_by(
            currency_from=from_currency,
            currency_to=to_currency,
            is_active=True
        ).order_by(cls.updated_at.desc()).first()
        
        return float(rate_record.rate) if rate_record else None


class FinancialReport(db.Model):
    """
    گزارش‌های مالی - بخش ۱۰
    """
    __tablename__ = 'financial_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    report_type = db.Column(db.String(50), nullable=False)  # monthly, yearly, transaction_history
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # TODO: Translate -  خلاصه گزارش
    total_income = db.Column(db.Numeric(20, 0), default=0)
    total_expense = db.Column(db.Numeric(20, 0), default=0)
    net_balance = db.Column(db.Numeric(20, 0), default=0)
    
    # TODO: Translate -  File گزارش
    file_path = db.Column(db.String(500))  #  Path File PDF/Excel
    file_format = db.Column(db.String(10), default='pdf')  # pdf, excel
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('financial_reports', lazy='dynamic'))
