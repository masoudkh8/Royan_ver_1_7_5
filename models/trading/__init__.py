"""
Metisma Trading Hall Models
=================================
مدل‌های داده‌ای برای تالار معاملاتی متیما

شامل:
- جفت‌های معاملاتی
- کیف پول‌های دیجیتال
- سفارش‌گذاری و معاملات
- داده‌های بازار

نسخه: 1.0.0
"""

from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

db = SQLAlchemy()


# =============================================================================
# ENUM Tables
# =============================================================================

class OrderType(db.Model):
    """انواع سفارش"""
    __tablename__ = 'order_type_enum'
    
    id = db.Column(db.Integer, primary_key=True)
    order_type = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f"<OrderType {self.order_type}>"


class OrderSide(db.Model):
    """سمت سفارش (خرید/فروش)"""
    __tablename__ = 'order_side_enum'
    
    id = db.Column(db.Integer, primary_key=True)
    side = db.Column(db.String(10), unique=True, nullable=False)
    
    def __repr__(self):
        return f"<OrderSide {self.side}>"


class OrderStatus(db.Model):
    """وضعیت‌های سفارش"""
    __tablename__ = 'order_status_enum'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f"<OrderStatus {self.status}>"


# =============================================================================
# TRADING MODELS
# =============================================================================

class TradingPair(db.Model):
    """
    جفت ارز/کالا قابل معامله
    مثال: BTC/USDT, GOLD/USD
    """
    __tablename__ = 'trading_pairs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    base_asset = db.Column(db.String(50), nullable=False)  # ارز پایه
    quote_asset = db.Column(db.String(50), nullable=False)  # ارز قیمت
    symbol = db.Column(db.String(20), unique=True, nullable=False)  # نماد نمایشی
    
    # مشخصات معامله
    min_order_size = db.Column(db.Numeric(20, 8), nullable=False)
    max_order_size = db.Column(db.Numeric(20, 8), nullable=False)
    price_precision = db.Column(db.Integer, default=2)  # دقت قیمت
    quantity_precision = db.Column(db.Integer, default=8)  # دقت مقدار
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # محدودیت‌ها
    trading_hours = db.Column(JSONB, default={})  # ساعات مجاز معامله
    allowed_user_levels = db.Column(JSONB, default=[])  # سطوح کاربری مجاز
    
    # آمار بازار (۲۴ ساعته)
    last_price = db.Column(db.Numeric(20, 8))
    price_change_24h = db.Column(db.Numeric(10, 4))  # درصد تغییر
    volume_24h = db.Column(db.Numeric(20, 8), default=0)
    high_24h = db.Column(db.Numeric(20, 8))
    low_24h = db.Column(db.Numeric(20, 8))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_trading_pairs_symbol', 'symbol', unique=True),
        db.Index('idx_trading_pairs_assets', 'base_asset', 'quote_asset'),
        db.Index('idx_trading_pairs_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<TradingPair {self.symbol}>"


class TradingWallet(db.Model):
    """
    کیف پول داخلی کاربران برای معاملات
    هر کاربر یک کیف پول با موجودی چندارزی دارد
    """
    __tablename__ = 'trading_wallets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, unique=True)
    
    # موجودی‌ها به صورت JSONB: {"USDT": 1000.50, "BTC": 0.05}
    balances = db.Column(JSONB, default={})
    locked_balances = db.Column(JSONB, default={})  # موجودی قفل‌شده در سفارش‌ها
    
    # اعتبار
    credit_limit = db.Column(db.Numeric(20, 8), default=0)
    used_credit = db.Column(db.Numeric(20, 8), default=0)
    
    # آمار معاملاتی
    total_trades = db.Column(db.Integer, default=0)
    total_volume = db.Column(db.Numeric(30, 8), default=0)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # مدیریت ریسک
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high
    daily_loss_limit = db.Column(db.Numeric(20, 8))  # حد ضرر روزانه
    daily_loss_current = db.Column(db.Numeric(20, 8), default=0)  # ضرر فعلی امروز
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_trading_wallets_user', 'user_id', unique=True),
        db.Index('idx_trading_wallets_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<TradingWallet User: {self.user_id}>"


class WalletTransaction(db.Model):
    """
    تراکنش‌های کیف پول
    ثبت تمام تغییرات موجودی
    """
    __tablename__ = 'wallet_transactions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trading_wallets.id'), nullable=False)
    
    transaction_type = db.Column(db.String(50), nullable=False)
    # deposit, withdrawal, trade_profit, trade_loss, fee, transfer, refund
    
    asset = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(20, 8), nullable=False)
    balance_before = db.Column(db.Numeric(20, 8), nullable=False)
    balance_after = db.Column(db.Numeric(20, 8), nullable=False)
    
    # ارجاع به سفارش یا معامله مرتبط
    related_order_id = db.Column(UUID(as_uuid=True))
    related_trade_id = db.Column(UUID(as_uuid=True))
    
    description = db.Column(db.Text)
    reference_id = db.Column(db.String(100))  # شناسه مرجع خارجی
    
    status = db.Column(db.String(50), default='completed')
    extra_data = db.Column(JSONB, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # رابطه
    wallet = db.relationship('TradingWallet', backref='transactions')
    
    __table_args__ = (
        db.Index('idx_wallet_transactions_wallet', 'wallet_id'),
        db.Index('idx_wallet_transactions_type', 'transaction_type'),
        db.Index('idx_wallet_transactions_time', 'created_at'),
        db.Index('idx_wallet_transactions_status', 'status'),
    )
    
    def __repr__(self):
        return f"<WalletTransaction {self.transaction_type} - {self.amount} {self.asset}>"


class TradeOrder(db.Model):
    """
    سفارش معامله
    پشتیبانی از انواع سفارش: Market, Limit, Stop-Limit
    """
    __tablename__ = 'trade_orders'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    trading_pair_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trading_pairs.id'), nullable=False)
    
    # نوع سفارش
    type_id = db.Column(db.Integer, db.ForeignKey('order_type_enum.id'), nullable=False)
    order_type = db.relationship('OrderType', backref='orders')
    
    # سمت سفارش
    side_id = db.Column(db.Integer, db.ForeignKey('order_side_enum.id'), nullable=False)
    side = db.relationship('OrderSide', backref='orders')
    
    # قیمت و مقدار
    price = db.Column(db.Numeric(20, 8))  # برای Limit orders
    quantity = db.Column(db.Numeric(20, 8), nullable=False)
    filled_quantity = db.Column(db.Numeric(20, 8), default=0)
    remaining_quantity = db.Column(db.Numeric(20, 8), nullable=False)
    
    # قیمت‌های شرطی
    stop_price = db.Column(db.Numeric(20, 8))  # برای Stop orders
    trigger_price = db.Column(db.Numeric(20, 8))  # قیمتی که سفارش فعال شده
    
    # وضعیت
    status_id = db.Column(db.Integer, db.ForeignKey('order_status_enum.id'), default=1)
    status = db.relationship('OrderStatus', backref='orders')
    
    # زمان‌بندی
    time_in_force = db.Column(db.String(20), default='GTC')  # GTC, IOC, FOK
    expires_at = db.Column(db.DateTime)
    
    # مالی
    fee_rate = db.Column(db.Numeric(10, 6), default=0.001)  # کارمزد
    total_fee = db.Column(db.Numeric(20, 8), default=0)
    average_fill_price = db.Column(db.Numeric(20, 8))
    
    # متادیتا
    client_order_id = db.Column(db.String(100), unique=True)  # شناسه سفارش از سمت کلاینت
    notes = db.Column(db.Text)
    extra_data = db.Column(JSONB, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # روابط
    trades = db.relationship('Trade', backref='order', lazy='dynamic')
    trading_pair = db.relationship('TradingPair', backref='orders')
    
    __table_args__ = (
        db.Index('idx_trade_orders_user', 'user_id'),
        db.Index('idx_trade_orders_pair', 'trading_pair_id'),
        db.Index('idx_trade_orders_status', 'status_id'),
        db.Index('idx_trade_orders_side', 'side_id'),
        db.Index('idx_trade_orders_created', 'created_at'),
        db.Index('idx_trade_orders_client', 'client_order_id', unique=True),
    )
    
    def __repr__(self):
        return f"<TradeOrder {self.side.side} {self.quantity} {self.trading_pair_id}>"


class Trade(db.Model):
    """
    معامله انجام‌شده
    نتیجه مچ شدن دو سفارش خرید و فروش
    """
    __tablename__ = 'trades'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    trading_pair_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trading_pairs.id'), nullable=False)
    
    # سفارش‌های طرفین
    maker_order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trade_orders.id'), nullable=False)
    taker_order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trade_orders.id'), nullable=False)
    
    # اطلاعات معامله
    price = db.Column(db.Numeric(20, 8), nullable=False)
    quantity = db.Column(db.Numeric(20, 8), nullable=False)
    quote_amount = db.Column(db.Numeric(20, 8), nullable=False)  # price * quantity
    
    # کارمزدها
    maker_fee = db.Column(db.Numeric(20, 8), default=0)
    taker_fee = db.Column(db.Numeric(20, 8), default=0)
    
    # نقش‌ها
    maker_user_id = db.Column(UUID(as_uuid=True), nullable=False)
    taker_user_id = db.Column(UUID(as_uuid=True), nullable=False)
    
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # روابط
    trading_pair = db.relationship('TradingPair', backref='trades')
    maker_order = db.relationship('TradeOrder', foreign_keys=[maker_order_id], backref='maker_trades')
    taker_order = db.relationship('TradeOrder', foreign_keys=[taker_order_id], backref='taker_trades')
    
    __table_args__ = (
        db.Index('idx_trades_pair', 'trading_pair_id'),
        db.Index('idx_trades_maker', 'maker_order_id'),
        db.Index('idx_trades_taker', 'taker_order_id'),
        db.Index('idx_trades_time', 'executed_at'),
        db.Index('idx_trades_maker_user', 'maker_user_id'),
        db.Index('idx_trades_taker_user', 'taker_user_id'),
    )
    
    def __repr__(self):
        return f"<Trade {self.quantity} @ {self.price}>"


class MarketData(db.Model):
    """
    داده‌های تاریخی بازار برای نمودارها
    کندل‌های قیمتی (OHLCV)
    """
    __tablename__ = 'market_data'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_pair_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trading_pairs.id'), nullable=False)
    
    # تایم‌فریم
    timeframe = db.Column(db.String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    
    # زمان شروع کندل
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # داده‌های OHLCV
    open_price = db.Column(db.Numeric(20, 8), nullable=False)
    high_price = db.Column(db.Numeric(20, 8), nullable=False)
    low_price = db.Column(db.Numeric(20, 8), nullable=False)
    close_price = db.Column(db.Numeric(20, 8), nullable=False)
    volume = db.Column(db.Numeric(20, 8), default=0)
    quote_volume = db.Column(db.Numeric(30, 8), default=0)
    
    # تعداد معاملات
    trade_count = db.Column(db.Integer, default=0)
    
    # داده‌های اضافی
    vwap = db.Column(db.Numeric(20, 8))  # Volume Weighted Average Price
    extra_data = db.Column(JSONB, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # رابطه
    trading_pair = db.relationship('TradingPair', backref='market_data')
    
    __table_args__ = (
        db.Index('idx_market_data_pair_time', 'trading_pair_id', 'timestamp'),
        db.Index('idx_market_data_timeframe', 'timeframe'),
        db.UniqueConstraint('trading_pair_id', 'timeframe', 'timestamp', name='uq_pair_timeframe_time'),
    )
    
    def __repr__(self):
        return f"<MarketData {self.trading_pair_id} {self.timeframe} {self.timestamp}>"


class TradingSetting(db.Model):
    """
    تنظیمات کلی تالار معاملاتی
    """
    __tablename__ = 'trading_settings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(JSONB, nullable=False)
    
    description_fa = db.Column(db.Text)
    description_en = db.Column(db.Text)
    
    is_public = db.Column(db.Boolean, default=False)  # آیا کاربران می‌توانند ببینند
    category = db.Column(db.String(50), default='general')
    
    updated_by = db.Column(UUID(as_uuid=True))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_trading_settings_key', 'setting_key', unique=True),
        db.Index('idx_trading_settings_category', 'category'),
    )
    
    def __repr__(self):
        return f"<TradingSetting {self.setting_key}>"


# =============================================================================
# Helper Functions
# =============================================================================

def init_trading_db(app=None):
    """
    مقداردهی اولیه دیتابیس تالار معاملاتی
    ایجاد مقادیر پیش‌فرض ENUMها و تنظیمات
    """
    if app:
        db.init_app(app)
    
    # ایجاد انواع سفارش
    order_types = ['market', 'limit', 'stop_limit', 'stop_market']
    for otype in order_types:
        existing = OrderType.query.filter_by(order_type=otype).first()
        if not existing:
            db.session.add(OrderType(order_type=otype))
    
    # ایجاد سمت‌های سفارش
    sides = ['buy', 'sell']
    for side in sides:
        existing = OrderSide.query.filter_by(side=side).first()
        if not existing:
            db.session.add(OrderSide(side=side))
    
    # ایجاد وضعیت‌های سفارش
    statuses = ['pending', 'partially_filled', 'filled', 'cancelled', 'rejected', 'expired']
    for status in statuses:
        existing = OrderStatus.query.filter_by(status=status).first()
        if not existing:
            db.session.add(OrderStatus(status=status))
    
    # ایجاد تنظیمات پیش‌فرض
    default_settings = [
        {
            'key': 'trading_enabled',
            'value': True,
            'desc_fa': 'فعال بودن تالار معاملاتی',
            'desc_en': 'Trading hall enabled',
            'category': 'general'
        },
        {
            'key': 'default_fee_rate',
            'value': 0.001,
            'desc_fa': 'کارمزد پیش‌فرض معاملات',
            'desc_en': 'Default trading fee rate',
            'category': 'fees'
        },
        {
            'key': 'max_orders_per_user',
            'value': 100,
            'desc_fa': 'حداکثر سفارش‌های باز برای هر کاربر',
            'desc_en': 'Maximum open orders per user',
            'category': 'limits'
        }
    ]
    
    for setting in default_settings:
        existing = TradingSetting.query.filter_by(setting_key=setting['key']).first()
        if not existing:
            db.session.add(TradingSetting(
                setting_key=setting['key'],
                setting_value=setting['value'],
                description_fa=setting['desc_fa'],
                description_en=setting['desc_en'],
                category=setting['category'],
                is_public=True
            ))
    
    db.session.commit()
