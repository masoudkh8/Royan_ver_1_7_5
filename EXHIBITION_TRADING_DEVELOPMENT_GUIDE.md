# 📚 مستند جامع توسعه نمایشگاه آنلاین و تالار معاملاتی متیما

## فهرست مطالب
1. [معرفی](#۱-معرفی)
2. [معماری سیستم](#۲-معماری-سیستم)
3. [مدل‌های داده‌ای](#۳-مدل-های-داده‌ای)
4. [نقشه راه توسعه](#۴-نقشه-راه-توسعه)
5. [راهنمای پیاده‌سازی فاز به فاز](#۵-راهنمای-پیاده‌سازی-فاز-به-فاز)
6. [API Design](#۶-api-design)
7. [ملاحظات فنی](#۷-ملاحظات-فنی)
8. [امنیت و بهینه‌سازی](#۸-امنیت-و-بهینه‌سازی)

---

## ۱. معرفی

### ۱.۱ هدف پروژه
ایجاد دو بخش مستقل اما یکپارچه:
- **نمایشگاه آنلاین (Exhibition Hall)**: پلتفرم برگزاری نمایشگاه‌های مجازی با غرفه‌های تعاملی
- **تالار معاملاتی (Trading Hall)**: سیستم معاملات بلادرنگ با قابلیت Order Matching

### ۱.۲ اصول طراحی
- ✅ **طراحی اول، پیاده‌سازی بعد**: مدل‌ها از قبل تعریف شده‌اند
- ✅ **توسعه پلکانی**: MVP → حرفه‌ای → پیشرفته
- ✅ **جداسازی کامل**: ماژول‌ها مستقل از هسته اصلی
- ✅ **مقیاس‌پذیری**: پشتیبانی از رشد سریع کاربران و داده‌ها

---

## ۲. معماری سیستم

### ۲.۱ دیاگرام کلی
```
┌─────────────────────────────────────────────────────────────┐
│                      Metisma Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Exhibition Hall │         │   Trading Hall   │          │
│  │                  │         │                  │          │
│  │  • Exhibitions   │         │  • TradingPairs  │          │
│  │  • Booths        │         │  • Orders        │          │
│  │  • Visits        │         │  • Trades        │          │
│  │  • Interactions  │         │  • Wallets       │          │
│  │  • Appointments  │         │  • Market Data   │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                              │                   │
│           └──────────┬───────────────────┘                   │
│                      │                                       │
│              ┌───────▼────────┐                             │
│              │  Shared Core   │                             │
│              │  • Users       │                             │
│              │  • Wallets     │                             │
│              │  • Products    │                             │
│              └────────────────┘                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### ۲.۲ تکنولوژی‌های پیشنهادی

#### برای نمایشگاه:
- **Frontend**: Three.js (برای 3D), React/Vue, WebSocket (برای چت زنده)
- **Backend**: Flask + Celery (برای پردازش‌های پس‌زمینه)
- **Database**: PostgreSQL + Redis (برای کش)
- **Media**: AWS S3 یا معادل داخلی

#### برای تالار معامله:
- **Real-time Engine**: Redis Pub/Sub + WebSocket
- **Matching Engine**: Python + asyncio یا Go/Rust برای performance بالا
- **Database**: PostgreSQL (برای داده‌های پایا) + Redis (برای Order Book)
- **Message Queue**: RabbitMQ یا Kafka

---

## ۳. مدل‌های داده‌ای

### ۳.۱ مدل‌های نمایشگاه (۶ جدول)

| جدول | توضیح | تعداد فیلد |
|------|-------|-----------|
| `exhibitions` | نمایشگاه‌های کلی | ۱۸ فیلد |
| `booths` | غرفه‌های نمایشگاه | ۲۵ فیلد |
| `booth_visits` | بازدید از غرفه | ۱۲ فیلد |
| `booth_interactions` | تعاملات کاربران | ۸ فیلد |
| `booth_appointments` | قرارهای ملاقات | ۱۴ فیلد |
| `exhibition_visits` | بازدید کلی | ۱۰ فیلد |

**رابطه‌ها:**
- هر Exhibition → چندین Booth
- هر Booth → چندین Visit, Interaction, Appointment
- Polymorphic Owner: booth.owner_type + booth.owner_id

### ۳.۲ مدل‌های تالار معامله (۷ جدول)

| جدول | توضیح | تعداد فیلد |
|------|-------|-----------|
| `trading_pairs` | جفت‌های معاملاتی | ۱۶ فیلد |
| `trading_wallets` | کیف پول کاربران | ۱۳ فیلد |
| `wallet_transactions` | تراکنش‌ها | ۱۳ فیلد |
| `trade_orders` | سفارش‌ها | ۲۰ فیلد |
| `trades` | معاملات انجام‌شده | ۱۴ فیلد |
| `market_data` | داده‌های بازار | ۱۱ فیلد |
| `trading_settings` | تنظیمات | ۶ فیلد |

**رابطه‌ها:**
- هر User → یک TradingWallet
- هر Wallet → چندین Transaction
- هر TradingPair → چندین Order, Trade, MarketData
- هر Order → چندین Trade

### ۳.۳ ENUM Lookup Tables
- `exhibition_status_enum`: draft, active, paused, ended, archived
- `booth_type_enum`: standard, premium, vip, custom_3d, interactive
- `order_type_enum`: market, limit, stop_loss, take_profit, stop_limit
- `order_side_enum`: buy, sell
- `order_status_enum`: pending, partial_filled, filled, cancelled, rejected, expired

---

## ۴. نقشه راه توسعه

### 🎯 فاز ۱: MVP (حداقل محصول قابل ارائه) - ۴-۶ هفته

#### نمایشگاه:
- [ ] CRUD نمایشگاه‌ها (Admin Panel)
- [ ] CRUD غرفه‌ها (صاحبان کسب‌وکار)
- [ ] صفحه نمایش غرفه (Public View)
- [ ] سیستم بازدید ساده (بدون تحلیل پیشرفته)
- [ ] فرم تماس ساده (Lead Generation)

#### تالار معامله:
- [ ] تعریف جفت‌های معاملاتی (Admin)
- [ ] کیف پول ساده (واریز/برداشت دستی)
- [ ] سفارش Limit و Market
- [ ] مچینگ ساده (First-Come-First-Serve)
- [ ] نمایش تاریخچه معاملات

#### زیرساخت:
- [ ] Migration دیتابیس
- [ ] APIهای پایه RESTful
- [ ] احراز هویت و مجوزها
- [ ] لاگ‌گیری پایه

### 🚀 فاز ۲: نسخه حرفه‌ای - ۸-۱۰ هفته

#### نمایشگاه:
- [ ] غرفه‌های ۳بعدی ساده (Three.js)
- [ ] تور مجازی (Virtual Tour)
- [ ] چت زنده (WebSocket)
- [ ] سیستم قرار ملاقات (Calendar Integration)
- [ ] آنالیز بازدید (Dashboard)
- [ ] گیمیفیکیشن (امتیاز، نشان)

#### تالار معامله:
- [ ] Order Book بلادرنگ (WebSocket)
- [ ] انواع سفارش پیشرفته (Stop Loss, Take Profit)
- [ ] نمودار قیمت (Candlestick Chart)
- [ ] کارمزدهای پویا
- [ ] تسویه خودکار
- [ ] مدیریت ریسک (Daily Loss Limit)

#### زیرساخت:
- [ ] Redis Caching
- [ ] Celery Tasks
- [ ] Rate Limiting
- [ ] Monitoring & Alerts

### 🌟 فاز ۳: نسخه پیشرفته - ۱۲-۱۶ هفته

#### نمایشگاه:
- [ ] غرفه‌های کاملاً تعاملی ۳بعدی
- [ ] آواتارهای کاربران
- [ ] رویدادهای زنده (Webinar, Live Stream)
- [ ] هوش مصنوعی برای پیشنهاد غرفه‌ها
- [ ] واقعیت افزوده (AR) برای محصولات

#### تالار معامله:
- [ ] Matching Engine با Performance بالا (Go/Rust)
- [ ] معاملات مارجین (اهرم)
- [ ] API عمومی برای Botها
- [ ] پرتفوی و تحلیل سود/زیان
- [ ] گزارش‌های مالیاتی

#### یکپارچگی:
- [ ] اتصال نمایشگاه به تالار (معامله مستقیم از غرفه)
- [ ] اشتراک‌گذاری داده‌ها بین ماژول‌ها
- [ ] Dashboard یکپارچه برای کاربران

---

## ۵. راهنمای پیاده‌سازی فاز به فاز

### ۵.۱ شروع کار (همین امروز!)

#### قدم ۱: ایجاد Migration
```bash
# در پوشه پروژه
python manage.py db migrate -m "Add exhibition and trading tables"
python manage.py db upgrade
```

#### قدم ۲: مقداردهی اولیه ENUMها
```python
from models import init_exhibition_trading_db
init_exhibition_trading_db(app)
```

#### قدم ۳: تست مدل‌ها
```python
from models import Exhibition, Booth, TradingPair

# ساخت یک نمایشگاه تست
exhibition = Exhibition(
    title_fa="نمایشگاه تستی",
    title_en="Test Exhibition",
    start_date=datetime.utcnow(),
    end_date=datetime.utcnow() + timedelta(days=30)
)
db.session.add(exhibition)
db.session.commit()
```

### ۵.۲ توسعه فاز ۱ - هفته ۱-۲: نمایشگاه

#### فایل‌های مورد نیاز:
```
routes/
  ├── exhibition.py          # Routeهای نمایشگاه
  └── booth.py               # Routeهای غرفه

templates/
  ├── exhibition/
  │   ├── list.html          # لیست نمایشگاه‌ها
  │   ├── detail.html        # جزئیات نمایشگاه
  │   └── booth_view.html    # مشاهده غرفه
  └── booth/
      ├── create.html        # ساخت غرفه
      └── edit.html          # ویرایش غرفه

static/
  └── js/
      └── exhibition.js      # جاوااسکریپت نمایشگاه
```

#### APIهای پایه:
```python
# routes/exhibition.py

@bp.route('/api/exhibitions', methods=['GET'])
def get_exhibitions():
    """دریافت لیست نمایشگاه‌ها"""
    status = request.args.get('status', 'active')
    exhibitions = Exhibition.query.filter_by(status=status).all()
    return jsonify([...])

@bp.route('/api/exhibitions', methods=['POST'])
@auth_required
def create_exhibition():
    """ساخت نمایشگاه جدید (Admin)"""
    data = request.get_json()
    exhibition = Exhibition(**data)
    db.session.add(exhibition)
    db.session.commit()
    return jsonify(exhibition.id), 201

@bp.route('/api/booths', methods=['POST'])
@auth_required
def create_booth():
    """ساخت غرفه جدید"""
    data = request.get_json()
    booth = Booth(**data)
    db.session.add(booth)
    db.session.commit()
    return jsonify(booth.id), 201
```

### ۵.۳ توسعه فاز ۱ - هفته ۳-۴: تالار معامله

#### فایل‌های مورد نیاز:
```
routes/
  ├── trading.py             # Routeهای معامله
  └── wallet.py              # Routeهای کیف پول

templates/
  ├── trading/
  │   ├── dashboard.html     # داشبورد معامله
  │   ├── order_book.html    # دفتر سفارشات
  │   └── chart.html         # نمودار قیمت
  └── wallet/
      ├── balance.html       # موجودی
      └── transactions.html  # تراکنش‌ها

utils/
  └── matching_engine.py     # موتور مچینگ ساده
```

#### موتور مچینگ ساده:
```python
# utils/matching_engine.py

class SimpleMatchingEngine:
    def __init__(self):
        self.order_books = {}  # {trading_pair_id: {'bids': [], 'asks': []}}
    
    def add_order(self, order):
        """افزودن سفارش به دفتر"""
        pair_id = order.trading_pair_id
        if pair_id not in self.order_books:
            self.order_books[pair_id] = {'bids': [], 'asks': []}
        
        book = self.order_books[pair_id]
        if order.side == 'buy':
            book['bids'].append(order)
            book['bids'].sort(key=lambda x: x.price, reverse=True)
        else:
            book['asks'].append(order)
            book['asks'].sort(key=lambda x: x.price)
        
        # تلاش برای مچ
        return self.match_orders(pair_id)
    
    def match_orders(self, pair_id):
        """مچ کردن سفارش‌ها"""
        book = self.order_books.get(pair_id)
        if not book:
            return []
        
        trades = []
        while book['bids'] and book['asks']:
            bid = book['bids'][0]
            ask = book['asks'][0]
            
            if bid.price >= ask.price:
                # مچ اتفاق افتاد
                quantity = min(bid.remaining_quantity, ask.remaining_quantity)
                price = ask.price  # قیمت فروشنده
                
                trade = self.create_trade(bid, ask, quantity, price)
                trades.append(trade)
                
                # بروزرسانی سفارش‌ها
                bid.filled_quantity += quantity
                bid.remaining_quantity -= quantity
                ask.filled_quantity += quantity
                ask.remaining_quantity -= quantity
                
                # حذف سفارش‌های پرشده
                if bid.remaining_quantity == 0:
                    book['bids'].pop(0)
                if ask.remaining_quantity == 0:
                    book['asks'].pop(0)
            else:
                break
        
        return trades
```

---

## ۶. API Design

### ۶.۱ نمایشگاه

#### Public APIs
```
GET    /api/exhibitions              # لیست نمایشگاه‌ها
GET    /api/exhibitions/<id>         # جزئیات نمایشگاه
GET    /api/exhibitions/<id>/booths  # غرفه‌های نمایشگاه
GET    /api/booths/<slug>            # مشاهده غرفه
POST   /api/booths/<id>/visit        # ثبت بازدید
POST   /api/booths/<id>/contact      # ارسال پیام به غرفه
```

#### Protected APIs
```
POST   /api/exhibitions              # ساخت نمایشگاه (Admin)
PUT    /api/exhibitions/<id>         # ویرایش نمایشگاه
DELETE /api/exhibitions/<id>         # حذف نمایشگاه

POST   /api/booths                   # ساخت غرفه
PUT    /api/booths/<id>              # ویرایش غرفه
DELETE /api/booths/<id>              # حذف غرفه

GET    /api/booths/<id>/analytics    # آنالیز غرفه (Owner)
POST   /api/booths/<id>/appointments # ساخت قرار ملاقات
```

### ۶.۲ تالار معامله

#### Public APIs
```
GET    /api/trading/pairs            # لیست جفت‌ها
GET    /api/trading/pairs/<symbol>   # جزئیات جفت
GET    /api/trading/orderbook/<pair> # دفتر سفارشات
GET    /api/trading/trades/<pair>    # تاریخچه معاملات
GET    /api/trading/marketdata/<pair># داده‌های بازار
```

#### Protected APIs
```
POST   /api/trading/orders           # ثبت سفارش جدید
GET    /api/trading/orders           # لیست سفارش‌های کاربر
DELETE /api/trading/orders/<id>      # لغو سفارش

GET    /api/trading/wallet           # موجودی کیف پول
GET    /api/trading/wallet/transactions # تراکنش‌ها

GET    /api/trading/portfolio        # پرتفوی کاربر
```

---

## ۷. ملاحظات فنی

### ۷.۱ Performance

#### بهینه‌سازی دیتابیس:
- ✅ ایندکس‌های مناسب روی فیلدهای پرجستجو
- ✅ Partitioning برای جداول بزرگ (trades, market_data)
- ✅ Connection Pooling
- ✅ Query Optimization

#### Caching Strategy:
```python
# Redis Cache Keys
CACHE_KEYS = {
    'exhibition_detail': 'exhibition:{id}',
    'booth_detail': 'booth:{slug}',
    'order_book': 'orderbook:{pair_id}',
    'market_data': 'marketdata:{pair_id}:{timeframe}',
    'user_wallet': 'wallet:{user_id}',
}

# TTL مقادیر مختلف
CACHE_TTL = {
    'exhibition_detail': 300,      # 5 دقیقه
    'booth_detail': 300,
    'order_book': 1,               # 1 ثانیه (بلادرنگ)
    'market_data': 60,             # 1 دقیقه
    'user_wallet': 60,
}
```

### ۷.۲ Real-time Updates

#### WebSocket Events:
```javascript
// Client-side events
const TRADING_EVENTS = {
    'ORDER_BOOK_UPDATE': 'orderbook:update',
    'NEW_TRADE': 'trade:new',
    'ORDER_FILLED': 'order:filled',
    'ORDER_CANCELLED': 'order:cancelled',
    'WALLET_UPDATE': 'wallet:update',
};

// Server-side emit
@socketio.on('connect')
def handle_connect():
    join_room('trading_pair:BTC_USD')
    emit('connected', {'status': 'ok'})

def broadcast_orderbook_update(pair_id):
    data = get_orderbook_snapshot(pair_id)
    emit('orderbook:update', data, room=f'trading_pair:{pair_id}')
```

### ۷.۳ امنیت

#### احراز هویت و مجوزها:
```python
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def trading_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        
        # بررسی داشتن کیف پول فعال
        wallet = TradingWallet.query.filter_by(
            user_id=current_user['id'],
            is_active=True
        ).first()
        
        if not wallet:
            return jsonify({'error': 'Trading wallet required'}), 403
        
        # بررسی احراز هویت برای معاملات
        if not wallet.is_verified:
            return jsonify({'error': 'Verification required'}), 403
        
        return f(*args, **kwargs)
    return decorated
```

#### Rate Limiting:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# محدودیت برای APIهای حساس
@bp.route('/api/trading/orders', methods=['POST'])
@limiter.limit("10 per minute")
@trading_required
def create_order():
    ...
```

---

## ۸. امنیت و بهینه‌سازی

### ۸.۱ امنیت داده‌ها

#### رمزنگاری:
- ✅ پسوردها: bcrypt/argon2
- ✅ اطلاعات حساس: AES-256
- ✅ ارتباطات: HTTPS/TLS 1.3

#### جلوگیری از حملات رایج:
- ✅ SQL Injection: SQLAlchemy ORM
- ✅ XSS: Escape outputs, CSP headers
- ✅ CSRF: CSRF tokens
- ✅ DDoS: Rate limiting, CDN

### ۸.۲ مانیتورینگ و لاگ

#### Structured Logging:
```python
import structlog

logger = structlog.get_logger()

def log_trade_execution(trade):
    logger.info(
        "trade_executed",
        trade_id=trade.id,
        pair=trade.trading_pair.symbol,
        price=float(trade.price),
        quantity=float(trade.quantity),
        maker_user=trade.maker_user_id,
        taker_user=trade.taker_user_id,
    )
```

#### Metrics:
```python
# Prometheus Metrics
from prometheus_client import Counter, Histogram

TRADE_COUNTER = Counter('trades_total', 'Total trades', ['pair', 'side'])
ORDER_LATENCY = Histogram('order_latency_seconds', 'Order processing latency')

def record_trade(trade):
    TRADE_COUNTER.labels(
        pair=trade.trading_pair.symbol,
        side=trade.order.side
    ).inc()
```

### ۸.۳ Backup و Recovery

#### استراتژی بکاپ:
```yaml
Backup Schedule:
  - Database: Every 6 hours (full), Every 15 minutes (incremental)
  - Files: Daily
  - Retention: 30 days
  
Recovery Time Objective (RTO): < 4 hours
Recovery Point Objective (RPO): < 15 minutes
```

---

## 📝 چک‌لیست نهایی

### قبل از شروع کدنویسی:
- [ ] مدل‌ها ایمپورت و تست شدند ✅
- [ ] Migrationها آماده‌اند
- [ ] محیط توسعه تنظیم است
- [ ] داکیومنت مطالعه شد

### پایان فاز ۱ (MVP):
- [ ] نمایشگاه‌ها قابل ساخت و مشاهده‌اند
- [ ] غرفه‌ها قابل مدیریت‌اند
- [ ] جفت‌های معاملاتی تعریف شده‌اند
- [ ] سفارش‌گذاری و مچینگ کار می‌کند
- [ ] کیف پول‌ها فعال‌اند

### پایان فاز ۲ (Professional):
- [ ] چت زنده و قرار ملاقات فعال است
- [ ] Order Book بلادرنگ داریم
- [ ] نمودارهای قیمت داریم
- [ ] آنالیز و گزارش‌گیری داریم

### پایان فاز ۳ (Advanced):
- [ ] غرفه‌های ۳بعدی کامل
- [ ] Matching Engine پرسرعت
- [ ] معاملات مارجین
- [ ] هوش مصنوعی و پیشنهادات

---

## 🎉 نتیجه‌گیری

این مستند نقشه راه کاملی برای توسعه نمایشگاه آنلاین و تالار معاملاتی متیما است. با پیروی از این راهنما، می‌توانید به صورت پلکانی و بدون سردرگمی، این دو بخش مهم را به پلتفرم اضافه کنید.

**نکته کلیدی:** مدل‌ها از قبل طراحی شده‌اند و نیازی به تغییر ندارند. فقط کافیست منطق کسب‌وکار و UI را پیاده‌سازی کنید.

موفق باشید! 🚀
