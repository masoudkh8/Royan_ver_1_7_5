# 🏗️ نقشه جامع فنی پلتفرم متیما (Metisma Technical Master Plan)

> **نسخه:** 1.0  
> **تاریخ به‌روزرسانی:** 2025  
> **وضعیت:** Production-Ready  
> **مخاطب:** طراحان، توسعه‌دهندگان، معماران سیستم  

---

## 📊 خلاصه اجرایی (Executive Summary)

متیما یک پلتفرم **Enterprise-Grade** برای تجارت بین‌المللی است که با معماری ماژولار و مقیاس‌پذیر طراحی شده است. این پروژه شامل:

| شاخص | تعداد | توضیحات |
|------|-------|---------|
| **فایل‌های Python** | 83+ | مدل‌ها، Routes، Services، Utils |
| **مدل‌های داده‌ای** | 26+ | 60+ جدول دیتابیس با روابط پیچیده |
| **قالب‌های HTML** | 65 | Templateهای Jinja2 با پشتیبانی PWA |
| **Routes/Endpoints** | 19+ | 50+ endpoint فعال |
| **سرویس‌های Docker** | 6 | Web, Worker, Beat, Flower, Redis, PostgreSQL |
| **زبان‌ها** | 2 | فارسی (fa_IR) و انگلیسی (en) |

---

## 🧱 1. معماری کلی سیستم (System Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer / Nginx                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application (Gunicorn)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Route     │  │   Route     │  │   Route     │          │
│  │   Users     │  │   Admin     │  │   Trading   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │     Redis       │ │     Celery      │
│   (Database)    │ │  (Cache/Queue)  │ │    (Worker)     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### لایه‌های اصلی:

| لایه | فناوری | مسئولیت |
|------|--------|---------|
| **Presentation** | Jinja2 + Tailwind CSS 4 | رندرینگ صفحات، UI/UX |
| **Application** | Flask 2.3.3 | منطق کسب‌وکار، Routing |
| **Service** | Custom Python Modules | Email, SMS, AI, Trading Engine |
| **Data Access** | SQLAlchemy 2.0 | ORM، Migrationها |
| **Infrastructure** | Docker + Gunicorn + Eventlet | Deployment، Real-time |

---

## 🛠️ 2. پشته تکنولوژی (Technology Stack)

### Backend (پایتون)

| کتابخانه | نسخه | کاربرد |
|----------|------|--------|
| **Flask** | 2.3.3 | فریم‌ورک اصلی وب |
| **SQLAlchemy** | 2.0.46 | ORM برای دیتابیس |
| **Flask-Migrate** | 4.1.0 | مدیریت Migrationهای Alembic |
| **Flask-Login** | 0.6.3 | مدیریت Session کاربران |
| **Flask-Mail** | 0.9.1 | ارسال ایمیل |
| **Flask-SocketIO** | 5.3.6 | ارتباطات Real-time |
| **Flask-Limiter** | 4.1.1 | Rate Limiting |
| **Flask-Caching** | 2.3.1 | کشینگ با Redis |
| **Flask-Babel** | 4.0.0 | چندزبانه (i18n) |
| **Flask-WTF** | 1.2.1 | فرم‌ها و CSRF Protection |
| **Flask-ReCaptcha** | 0.4.2 | محافظت در برابر ربات‌ها |
| **Celery** | 5.4.0 | پردازش ناهمگام (Async Tasks) |
| **Redis** | 5.2.1 | Broker برای Celery + Cache |
| **Psycopg2** | 2.9.9 | درایور PostgreSQL |
| **Authlib** | 1.7.2 | احراز هویت OAuth |
| **PyOTP** | 2.9.0 | احراز هویت دو مرحله‌ای (2FA) |
| **Pillow** | 10.2.0 | پردازش تصاویر |
| **Eventlet** | 0.41.0 | Async I/O برای SocketIO |
| **Gunicorn** | 21.2.0 | WSGI Server برای Production |

### Frontend

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **Tailwind CSS** | 4.3.0 | Styling Utility-First |
| **HTML5** | - | Templateهای Jinja2 |
| **JavaScript (Vanilla)** | ES6+ | تعاملات کلاینت |
| **Three.js** | - | گرافیک سه‌بعدی (Smart Map) |
| **PWA** | - | Progressive Web App (آفلاین) |

### DevOps & Infrastructure

| ابزار | کاربرد |
|-------|--------|
| **Docker** | Containerization |
| **Docker Compose** | Orchestration سرویس‌ها |
| **GitHub Actions** | CI/CD Pipeline |
| **PostgreSQL** | 15-alpine (دیتابیس اصلی) |
| **Redis** | 7-alpine (Cache + Queue) |
| **Nginx** | Reverse Proxy (در Production) |
| **Let's Encrypt** | SSL/TLS Certificates |

### Security & Quality

| ابزار | هدف |
|-------|-----|
| **Bandit** | اسکن امنیت کد پایتون |
| **Flake8** | Linting کد |
| **Black** | Format خودکار کد |
| **Mypy** | Type Checking |
| **Pytest** | Testing Framework |
| **Coverage** | گزارش پوشش تست |

---

## 📁 3. ساختار فایل‌ها و پوشه‌ها (Project Structure)

```
/workspace
├── app.py                          # نقطه شروع اصلی اپلیکیشن
├── wsgi.py                         # Entry Point برای Gunicorn
├── config.py                       # تنظیمات محیطی (Development/Production)
├── extensions.py                   # اولیه‌سازی افزونه‌های Flask
├── celery_app.py                   # تنظیمات Celery Worker
├── socketio_app.py                 # تنظیمات SocketIO
├── requirements.txt                # وابستگی‌های Python
├── package.json                    # وابستگی‌های Node.js (Tailwind)
├── docker-compose.yml              # تعریف سرویس‌های Docker
├── Dockerfile                      # Image ساخت اپلیکیشن
├── .env                            # متغیرهای محیطی (حساس)
├── .github/workflows/ci-cd.yml     # Pipeline خودکار CI/CD
│
├── models/                         # مدل‌های داده‌ای (SQLAlchemy)
│   ├── __init__.py                 # export همه مدل‌ها
│   ├── user.py                     # User, UserProfile, Role
│   ├── auth.py                     # Tokenها، Sessionها، ActivityLog
│   ├── product.py                  # Product, RFQ, RFQProposal
│   ├── order.py                    # Order, OrderStatus
│   ├── wallet.py                   # Wallet, Transaction, Escrow
│   ├── trust_score.py              # TrustScore (امتیاز اعتماد)
│   ├── gamification.py             # Badge, Challenge, Progress
│   ├── trade_credit.py             # CreditAccount, CreditTransaction
│   ├── consortium.py               # ConsortiumProject, Member
│   ├── course.py                   # Course, Lesson, Certificate
│   ├── lead.py                     # Lead, Campaign, Automation
│   ├── integration.py              # ExternalIntegration, Webhook
│   ├── ai_chat.py                  # Conversation, ChatMessage, AIRecommendation
│   ├── smart_map.py                # Country, CustomsData, TradeRoute
│   ├── data_intelligence.py        # MarketTrend, CompetitorAnalysis
│   ├── social.py                   # Post, Comment, Like, Follow
│   ├── magazine.py                 # Magazine, Issue, Subscription
│   ├── exhibition/                 # Exhibition, Booth, Visit
│   ├── trading/                    # TradingPair, TradeOrder, MarketData
│   └── ... (26+ مدل دیگر)
│
├── routes/                         # کنترلرهای HTTP (Blueprints)
│   ├── users/
│   │   ├── routes.py               # Routes اصلی کاربران (1912 خط!)
│   │   ├── auth.py                 # Login, Register, PasswordReset
│   │   ├── permissions_routes.py   # مدیریت دسترسی‌ها
│   │   └── utils.py                # توابع کمکی
│   ├── admin/
│   │   ├── routes.py               # داشبورد ادمین، مدیریت کاربران
│   │   ├── permissions.py          # RBAC Logic
│   │   └── requests.py             # درخواست‌های Premium
│   ├── trading/
│   │   └── routes.py               # تالار معاملات، سفارشات
│   ├── exhibition/
│   │   └── routes.py               # نمایشگاه آنلاین، غرفه‌ها
│   ├── social/
│   │   └── routes.py               # شبکه اجتماعی، Feed، Posts
│   ├── magazine/
│   │   └── routes.py               # مجله، مقالات، اشتراک
│   └── language.py                 # Language Switcher
│
├── services/                       # منطق کسب‌وکار (Business Logic)
│   ├── __init__.py
│   ├── access_control.py           # کنترل دسترسی پیشرفته
│   └── permissions.py              # سیاست‌های مجوز
│
├── metisma/services/               # سرویس‌های تخصصی
│   ├── email_service.py            # ارسال ایمیل (جایگزین Flask-Mail)
│   ├── trading_engine.py           # موتور تطبیق سفارشات
│   └── exhibition_services.py      # خدمات نمایشگاه
│
├── utils/                          # توابع عمومی
│   ├── translations.py             # مدیریت ترجمه‌ها
│   ├── fallback.py                 # مکانیزم Fallback
│   ├── language_switcher.py        # تغییر زبان
│   └── feature_flags.py            # Feature Flag System
│
├── templates/                      # قالب‌های Jinja2 (65 فایل)
│   ├── base_pwa.html               # Base Template با پشتیبانی PWA
│   ├── landing.html                # صفحه اصلی (2109 خط!)
│   ├── offline.html                # صفحه آفلاین
│   ├── users/                      # 30+ template کاربران
│   ├── admin/                      # 12+ template ادمین
│   ├── trading/                    # templateهای تالار معامله
│   ├── exhibition/                 # templateهای نمایشگاه
│   ├── magazine/                   # templateهای مجله
│   ├── components/                 # Componentهای قابل استفاده مجدد
│   └── email/                      # Template ایمیل‌ها
│
├── static/                         # فایل‌های استاتیک
│   ├── css/
│   │   ├── input.css               # Source Tailwind
│   │   └── output.css              # Compiled Tailwind (181KB)
│   ├── js/
│   │   ├── three.min.js            # کتابخانه Three.js
│   │   ├── countries.js            # داده‌های کشورها
│   │   └── sw.js                   # Service Worker برای PWA
│   ├── fonts/                      # فونت‌های Vazirmatn, Inter
│   ├── images/                     # تصاویر، لوگوها، آواتارها
│   ├── icons/                      # آیکون‌های SVG/PNG
│   └── textures/                   # Textureهای سه‌بعدی
│
├── translations/                   # فایل‌های ترجمه (i18n)
│   ├── fa_IR/LC_MESSAGES/messages.po
│   └── en/LC_MESSAGES/messages.po
│
├── scripts/                        # اسکریپت‌های کمکی
│   ├── seed_data.py                # تولید داده‌های نمونه
│   ├── seed_exhibition_trading.py  # Seed مخصوص نمایشگاه و تالار
│   └── ... 
│
├── tests/                          # تست‌های واحد و یکپارچه‌سازی
│   └── ... 
│
├── docs/                           # مستندات پروژه (30+ فایل MD)
│   ├── BUSINESS_MASTERPLAN.md      # استراتژی کسب‌وکار
│   ├── API_DOCUMENTATION.md        # مستندات API
│   ├── PRODUCTION_SETUP_GUIDE.md   # راهنمای استقرار
│   └── ... 
│
├── logs/                           # لاگ‌های اپلیکیشن
├── uploads/                        # فایل‌های آپلودشده کاربران
└── instance/                       # دیتابیس SQLite (Development)
```

---

## 🗄️ 4. مدل‌های داده‌ای (Data Models)

### دسته‌بندی مدل‌ها:

#### الف) هسته مرکزی (Core)
| مدل | فیلدهای کلیدی | توضیحات |
|-----|--------------|---------|
| **User** | id, email, phone, role, trust_score, is_verified | کاربران با نقش‌های متعدد |
| **UserProfile** | user_id, bio, expertise, company, website | پروفایل تکمیلی |
| **Role** | name, permissions | نقش‌های RBAC |
| **TrustScore** | user_id, score, level, factors | امتیاز اعتماد 4 لایه‌ای |

#### ب) احراز هویت و امنیت (Auth & Security)
| مدل | کاربرد |
|-----|--------|
| **PasswordResetToken** | توکن بازیابی رمز عبور |
| **EmailVerificationToken** | تایید ایمیل |
| **LoginSession** | Sessionهای فعال کاربر |
| **ActivityLog** | لاگ فعالیت‌ها برای Audit |
| **TwoFactorBackupCode** | کدهای پشتیبان 2FA |

#### ج) محصولات و بازار (Marketplace)
| مدل | توضیحات |
|-----|---------|
| **Product** | کالاها با دسته‌بندی، قیمت، موجودی |
| **RFQ** | درخواست پیشنهاد قیمت (Request for Quotation) |
| **RFQProposal** | پیشنهادات ارسال‌شده برای RFQ |
| **FavoriteProduct** | علاقه‌مندی‌های کاربر |

#### د) مالی و پرداخت (Financial)
| مدل | کاربرد |
|-----|--------|
| **Wallet** | کیف پول چندارزی کاربران |
| **WalletTransaction** | تراکنش‌های واریز/برداشت |
| **EscrowTransaction** | پرداخت امن (واسطه) |
| **ExchangeRate** | نرخ لحظه‌ای ارزها |
| **TradeCreditAccount** | حساب اعتباری تجاری |
| **CreditTransaction** | تراکنش‌های اعتباری |

#### هـ) شبکه اجتماعی (Social Network)
| مدل | توضیحات |
|-----|---------|
| **Post** | پست‌های کاربران در فید |
| **Comment** | نظرات روی پست‌ها |
| **Like** | لایک‌ها |
| **Follow** | روابط فالو کردن |

#### و) آموزش و یادگیری (Learning Hub)
| مدل | کاربرد |
|-----|--------|
| **Course** | دوره‌های آموزشی |
| **CourseModule** | سرفصل‌های دوره |
| **CourseLesson** | درس‌های هر модуль |
| **Certificate** | گواهینامه‌های پایان دوره |
| **Webinar** | وبینارهای زنده |

#### ز) نمایشگاه و تالار معامله (Exhibition & Trading)
| مدل | توضیحات |
|-----|---------|
| **Exhibition** | رویدادهای نمایشگاهی |
| **Booth** | غرفه‌های دیجیتال |
| **BoothVisit** | بازدید از غرفه‌ها |
| **TradingPair** | جفت‌های معاملاتی |
| **TradeOrder** | سفارشات خرید/فروش |
| **MarketData** | داده‌های لحظه‌ای بازار |

#### ح) هوش مصنوعی و تحلیل (AI & Intelligence)
| مدل | کاربرد |
|-----|--------|
| **Conversation** | گفتگوهای کاربر با AI |
| **ChatMessage** | پیام‌های چت |
| **AIRecommendation** | توصیه‌های هوشمند |
| **MarketTrend** | روندهای بازار |
| **CompetitorAnalysis** | تحلیل رقبا |

---

## 🔌 5. Routes و Endpoints

### Blueprints اصلی:

| Blueprint | Prefix | مسئولیت | تعداد Routes |
|-----------|--------|---------|--------------|
| **users** | `/` | ثبت‌نام، ورود، پروفایل، داشبورد | 40+ |
| **admin** | `/admin` | مدیریت کاربران، محتوا، تنظیمات | 15+ |
| **trading** | `/trading` | تالار معامله، سفارشات، بازار | 10+ |
| **exhibition** | `/exhibition` | نمایشگاه، غرفه‌ها، بازدید | 8+ |
| **social** | `/social` | فید، پست‌ها، فالو | 12+ |
| **magazine** | `/magazine` | مقالات، اشتراک، تبلیغات | 6+ |

### Endpointهای مهم:

#### کاربران (Users)
```
GET  /                      # Landing Page
GET  /register              # ثبت‌نام
POST /register              # ارسال ثبت‌نام
GET  /login                 # ورود
POST /login                 # ارسال ورود
GET  /profile               # پروفایل کاربری
POST /profile/update        # به‌روزرسانی پروفایل
GET  /dashboard             # داشبورد شخصی
POST /upload/document       # آپلود مدارک
GET  /verify-email          # تایید ایمیل
POST /enable-2fa            # فعال‌سازی 2FA
```

#### ادمین (Admin)
```
GET  /admin/dashboard       # داشبورد ادمین
GET  /admin/users           # لیست کاربران
POST /admin/user/<id>/role  # تغییر نقش کاربر
GET  /admin/permissions     # مدیریت دسترسی‌ها
GET  /admin/premium-requests # درخواست‌های Premium
```

#### تالار معامله (Trading)
```
GET  /trading/market        # صفحه بازار
POST /trading/order         # ثبت سفارش معامله
GET  /trading/orders        # سفارشات کاربر
GET  /trading/portfolio     # پرتفوی کاربر
```

#### نمایشگاه (Exhibition)
```
GET  /exhibition/hall       # سالن نمایشگاه
GET  /exhibition/booth/<id> # جزئیات غرفه
POST /exhibition/visit      # ثبت بازدید
POST /exhibition/appointment # رزرو قرار ملاقات
```

---

## 🎨 6. طراحی UI/UX و Design System

### پالت رنگی:

| نام | کد HEX | کاربرد |
|-----|--------|--------|
| **Midnight Blue** | `#0B1120` | پس‌زمینه اصلی (Dark Mode) |
| **Dark Slate** | `#1E293B` | پس‌زمینه ثانویه |
| **Muted Turquoise** | `#2DD4BF` | رنگ اصلی (Primary) |
| **Champagne Gold** | `#D4AF37` | رنگ تأکیدی (Accent) |
| **Off-White** | `#F8FAFC` | متن اصلی |
| **Muted Red** | `#EF4444` | هشدارها و خطاها |

### فونت‌ها:

| زبان | فونت | وزن‌ها |
|------|------|--------|
| **فارسی** | Vazirmatn | Light, Regular, Bold |
| **انگلیسی** | Inter | 400, 500, 600, 700 |

### سبک طراحی:
- **Dark Luxury Tech**: ترکیبی از رابط‌های معاملاتی وال‌استریت و المان‌های علمی-تخیلی
- **مینیمالیسم عملکردی**: حذف عناصر غیرضروری، تمرکز بر داده‌ها
- **فضای منفی سخاوتمندانه**: القای حس لوکس بودن
- **Micro-interactions**: بازخورد بصری برای هر تعامل

---

## 🔐 7. امنیت و کنترل دسترسی (Security & RBAC)

### لایه‌های امنیتی:

1. **احراز هویت (Authentication)**
   - ایمیل/رمز عبور با الزامات پیچیدگی
   - تأیید ایمیل و شماره موبایل
   - 2FA با TOTP (Google Authenticator)
   - Backup Codes برای مواقع اضطراری

2. **مجوزها (Authorization)**
   - **RBAC (Role-Based Access Control)**: نقش‌های predefined
   - **Permission-Based**: دسترسی‌های ریزدانه
   - **Decorator**: `@role_required('ADMIN')`

3. **محافظت در برابر حملات**
   - **CSRF Protection**: توکن‌های خودکار
   - **Rate Limiting**: 100 درخواست/ساعت (pre-auth)
   - **reCAPTCHA v3**: تشخیص ربات
   - **SQL Injection Prevention**: SQLAlchemy ORM
   - **XSS Protection**: Jinja2 Auto-escaping

4. **امنیت داده‌ها**
   - رمزنگاری رمز عبور با bcrypt
   - HTTPS اجباری در Production
   - Secure Cookies (HttpOnly, SameSite)
   - Audit Logging تمام فعالیت‌ها

---

## ⚙️ 8. پیکربندی و Environment Variables

### متغیرهای حیاتی (.env):

```env
# Flask
SECRET_KEY=<random-secret-key>
FLASK_ENV=production
FLASK_DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-password>

# SMS
KAVENEGAR_API_KEY=<your-api-key>
AMOOTSMS_TOKEN=<your-token>

# reCAPTCHA
RECAPTCHA_SITE_KEY=<site-key>
RECAPTCHA_SECRET_KEY=<secret-key>

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# SocketIO
SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/0

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/1

# Uploads
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=52428800
```

---

## 🚀 9. راه‌اندازی و Deployment

### Development (محلی):

```bash
# 1. نصب وابستگی‌ها
pip install -r requirements.txt
npm install

# 2. راه‌اندازی دیتابیس
sudo -u postgres psql -c "CREATE DATABASE ports_db;"
export DATABASE_URL=postgresql://postgres:password@localhost:5432/ports_db

# 3. اجرای Redis
redis-server

# 4. Migrationها
flask db upgrade

# 5. کامپایل Tailwind
python build_tailwind.py

# 6. اجرای اپلیکیشن
python app.py
```

### Production (Docker):

```bash
# 1. کپی .env
cp .env.example .env

# 2. اجرای تمام سرویس‌ها
docker-compose up -d

# 3. مشاهده لاگ‌ها
docker-compose logs -f

# 4. دسترسی به Flower (مانیتورینگ Celery)
open http://localhost:5555
```

### CI/CD Pipeline:

```yaml
# GitHub Actions (/.github/workflows/ci-cd.yml)
- Test: pytest, flake8, black, mypy, bandit
- Build: Docker image
- Deploy: Push to registry + SSH deploy
```

---

## 📈 10. مانیتورینگ و سلامت سیستم

### Endpointهای سلامت:

| Endpoint | توضیحات |
|----------|---------|
| `GET /health` | بررسی سلامت دیتابیس، Redis، Celery |
| `GET /metrics` | متریک‌های Prometheus-style |

### لاگ‌برداری:

- **File Handler**: چرخشی (RotatingFileHandler) در `logs/app.log`
- **Console Handler**: خروجی استاندارد برای Docker
- **Format**: JSON ساختاریافته برای تحلیل

### مانیتورینگ Celery:

- **Flower**: داشبورد real-time برای workerها
- **PROMETHEUS**: متریک‌های سفارشی (اختیاری)

---

## 🧩 11. ویژگی‌های کلیدی پلتفرم

### 1. Trust Score System
- الگوریام پویا بر اساس 4 لایه:
  - **لایه 1**: تکمیل پروفایل
  - **لایه 2**: تأیید مدارک (KYC/KYB)
  - **لایه 3**: سابقه تعاملات موفق
  - **لایه 4**: توصیه‌نامه از اعضای نخبه

### 2. Gamification
- **Badges**: نشان‌های افتخار (Early Adopter, Verified Trader, Top Contributor)
- **Challenges**: چالش‌های فصلی با جوایز
- **Progress Bars**: نوار پیشرفت برای رسیدن به لول بعدی

### 3. Multi-language (i18n)
- پشتیبانی کامل از فارسی و انگلیسی
- ترجمه تمام رشته‌ها با Gettext
- تغییر زبان لحظه‌ای بدون Reload

### 4. Real-time Features
- **SocketIO**: چت زنده، نوتیفیکیشن‌های آنی
- **Market Data**: به‌روزرسانی لحظه‌ای قیمت‌ها
- **Notifications**: اعلان‌های push در browser

### 5. PWA Support
- Service Worker برای کشینگ
- کارکرد در حالت آفلاین
- Installable روی موبایل و دسکتاپ

---

## 📝 12. مستندات اضافی

| فایل | توضیحات |
|------|---------|
| `docs/BUSINESS_MASTERPLAN.md` | استراتژی کسب‌وکار و فلسفه پلتفرم |
| `docs/API_DOCUMENTATION.md` | مستندات کامل APIها |
| `docs/PRODUCTION_SETUP_GUIDE.md` | راهنمای استقرار در Production |
| `docs/FEATURE_FLAG_CICD_GUIDE.md` | سیستم Feature Flags |
| `docs/IMPLEMENTATION_ROADMAP.md` | نقشه راه پیاده‌سازی |
| `metisma/METISMA_MASTER_PLAN.md` | سند جامع استراتژی متیما |

---

## 🎯 13. چک‌لیست برای طراحان جدید

### قبل از شروع:
- [ ] مطالعه `BUSINESS_MASTERPLAN.md` برای درک فلسفه پلتفرم
- [ ] نصب Docker و Docker Compose
- [ ] آشنایی با Flask و SQLAlchemy
- [ ] آشنایی با Tailwind CSS 4

### هنگام توسعه:
- [ ] رعایت اصول RBAC در ایجاد Routes جدید
- [ ] استفاده از Feature Flags برای قابلیت‌های آزمایشی
- [ ] نوشتن تست برای کدهای جدید (pytest)
- [ ] به‌روزرسانی مستندات در صورت نیاز

### استانداردهای کدنویسی:
- [ ] رعایت PEP 8 برای پایتون
- [ ] استفاده از Type Hints
- [ ] کامنت‌گذاری برای توابع پیچیده
- [ ] جلوگیری از Hard-coded Values

---

## 📞 14. پشتیبانی و منابع

### منابع داخلی:
- **مستندات**: پوشه `/docs`
- **کد نمونه**: پوشه `/scripts`
- **ترجمه‌ها**: پوشه `/translations`

### جامعه:
- **GitHub Issues**: برای گزارش باگ و درخواست ویژگی
- **Discord/Slack**: کانال ارتباطی تیم (در صورت وجود)

---

> **شعار فنی:** *"اعتماد، مرزهای تجارت را جابه‌جا می‌کند."*  
> **متیما — جایی که تاجران واقعی گرد هم می‌آیند.**

---

*تهیه‌شده برای تیم توسعه متیما — نسخه 1.0 — 2025*
