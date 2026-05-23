# routes/users/routes.py
from flask_wtf.csrf import generate_csrf
from datetime import datetime
import pytz
tehran_tz = pytz.timezone('Asia/Tehran')
import os
import json
import secrets
from werkzeug.utils import secure_filename

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from extensions import limiter
from models import Message, Notification, db, user
from models.user import User, Role
from models.auth import PasswordResetToken, LoginSession, ActivityLog, EmailVerificationToken, TwoFactorBackupCode
from models.port import Port

from . import users_bp,root_bp

from config import Config
from PIL import Image
import requests

# reCAPTCHA validation helper
def verify_recaptcha(response_token):
    """Verify reCAPTCHA token with Google"""
    if not Config.RECAPTCHA_ENABLED or not response_token:
        return True  # Skip if disabled
    
    secret_key = Config.RECAPTCHA_SECRET_KEY
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    
    try:
        payload = {
            'secret': secret_key,
            'response': response_token
        }
        response = requests.post(verify_url, data=payload, timeout=5)
        result = response.json()
        return result.get('success', False) and result.get('score', 0) >= 0.5
    except Exception as e:
        current_app.logger.error(f"reCAPTCHA verification failed: {e}")
        return False


# ==============================
# دکوریتورهای دسترسی مبتنی بر نقش
# ==============================
def role_required(*roles):
    """دکوریتور برای محدود کردن دسترسی بر اساس نقش کاربر"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("لطفاً ابتدا وارد شوید.", "error")
                return redirect(url_for('users.login'))
            
            if current_user.role.value not in roles:
                flash("دسترسی غیرمجاز. این بخش مخصوص نقش‌های خاصی است.", "error")
                return redirect(url_for('users.profile'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==============================
# توابع کمکی برای آپلود امن فایل
# ==============================
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """بررسی پسوند فایل مجاز"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file, image_only=False):
    """اعتبارسنجی کامل فایل آپلود شده"""
    if not file or file.filename == '':
        return False, "فایلی انتخاب نشده است"
    
    # Determine allowed extensions based on type
    if image_only:
        allowed_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        max_size = current_app.config.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024)
        error_msg = "نوع فایل مجاز نیست (فقط JPG, PNG, GIF, WEBP)"
    else:
        allowed_exts = ALLOWED_EXTENSIONS
        max_size = MAX_FILE_SIZE
        error_msg = "نوع فایل مجاز نیست (فقط PDF, PNG, JPG)"
    
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_exts:
        return False, error_msg
    
    # بررسی اندازه فایل
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        size_mb = max_size / (1024 * 1024)
        return False, f"حجم فایل نباید بیشتر از {size_mb:.0f}MB باشد"
    
    return True, ""


# routes/users/routes.py یا app.py
@root_bp.route('/')
def main_page():
    return render_template('landingbase.html')


@users_bp.before_request
def make_session_permanent():
    """Make sessions permanent so they expire after PERMANENT_SESSION_LIFETIME"""
    session.permanent = True

"""
@users_bp.route('/create_first_admin', methods=['GET', 'POST'])
def create_first_admin():
    # فقط در محیط توسعه یا وقتی هیچ ادمینی وجود ندارد قابل دسترسی است
    if User.query.filter_by(role=Role.ADMIN, is_active=True).first():
        flash("There is already an admin.")
        return redirect(url_for('users.login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("❌ Please fill in all fields.")
            return redirect(url_for('users.create_first_admin'))

        if len(username) < 3:
            flash("❌ Username must be at least 3 characters long.")
            return redirect(url_for('users.create_first_admin'))

        if '@' not in email:
            flash("❌ The email address is invalid.")
            return redirect(url_for('users.create_first_admin'))

        if len(password) < 8:
            flash("❌ The password must be at least 8 characters long.")
            return redirect(url_for('users.create_first_admin'))

        if User.query.filter_by(username=username, is_active=True).first():
            flash("❌ Username already taken.")
            return redirect(url_for('users.create_first_admin'))

        if User.query.filter_by(email=email, is_active=True).first():
            flash("❌ Email already used.")
            return redirect(url_for('users.create_first_admin'))

        try:
            hashed = generate_password_hash(password)
            user = User(
                username=username,
                email=email,
                password_hash=hashed,
                role=Role.ADMIN,
                is_premium=True,
                is_active=True
            )

            db.session.add(user)
            db.session.commit()
            flash("✅ The first admin was created successfully. Please log in.")
            return redirect(url_for('admin.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin: {e}")
            flash("❌ An error occurred while creating the admin.")
            return redirect(url_for('users.create_first_admin'))

    return render_template('create_first_admin.html')
"""


@users_bp.route('/create_first_admin', methods=['GET', 'POST'])
def create_first_admin():
    if User.query.filter_by(role=Role.ADMIN, is_active=True).first():
        flash("قبلاً یک ادمین وجود دارد.")
        return redirect(url_for('users.login'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username, is_active=True).first():
            flash("❌ نام کاربری قبلاً گرفته شده.")
            return redirect(url_for('users.register'))

        if User.query.filter_by(email=email, is_active=True).first():
            flash("❌ ایمیل قبلاً استفاده شده.")
            return redirect(url_for('users.register'))

        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed,
            role=Role.ADMIN,
            is_premium=True
        )

        db.session.add(user)
        db.session.commit()
        flash("ادمین اول ایجاد شد.")
        return redirect(url_for('admin.login'))

    # ✅ Generate & inject CSRF token
    csrf_token = generate_csrf()
    return f'''
    <form method="post">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <input name="username" placeholder="نام کاربری" required><br>
        <input name="email" type="email" placeholder="ایمیل" required><br>
        <input name="password" type="password" placeholder="رمز عبور" required><br>
        <button type="submit">ایجاد ادمین</button>
    </form>
    '''


##############
# در routes/users/routes.py یا root_bp
@users_bp.route('/set-language')
def set_language():
    """Set user language preference"""
    lang = request.args.get('lang', 'fa')
    if lang in ['fa', 'en']:
        session['lang'] = lang
        # ریدایرکت به صفحه قبلی یا خانه
        next_page = request.args.get('next') or request.referrer or url_for('root.index')
        return redirect(next_page)
    return redirect(url_for('root.index'))





# -------------------------------
# ثبت نام
# -------------------------------
# Register (Request 2: Smart Multi-step Registration)
# ثبت‌نام پیشرفته با CAPTCHA و تأیید ایمیل
# -------------------------------
@users_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limiting for registration
def register():
    if current_user.is_authenticated:
        flash("You already have an account. Please log out first to register a new account.")
        return redirect(url_for('users.profile'))
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role')
        company = request.form.get('company', '').strip()
        country = request.form.get('country', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # New specialized fields
        expertise_area = request.form.get('expertise_area', '').strip()
        job_title = request.form.get('job_title', '').strip()
        bio = request.form.get('bio', '').strip()
        website = request.form.get('website', '').strip()
        
        # reCAPTCHA verification
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash("reCAPTCHA verification failed. Please try again.", "error")
            return redirect(url_for('users.register'))
        
        # Precise input validation (Request 2)
        errors = []
        
        # Username check
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if User.query.filter_by(username=username, is_active=True).first():
            errors.append("Username already taken.")
        
        # Email check
        if not email or '@' not in email:
            errors.append("Invalid email address.")
        if User.query.filter_by(email=email, is_active=True).first():
            errors.append("Email already used.")
        
        # Strong password check (Request 2)
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        else:
            # Password strength check
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            
            if not (has_upper and has_lower and has_digit):
                errors.append("Password should contain uppercase, lowercase, and numbers for better security.")
        
        # Role check
        if not role or not Role.has_value(role):
            errors.append("Invalid role selected.")
        
        # Phone check
        if phone and (not phone.isdigit() or len(phone.replace('+', '').replace('-', '')) < 10):
            errors.append("Invalid phone number.")
        
        # If there are errors, return to form
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('users.register'))
        
        # Create new user
        try:
            hashed = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed,
                role=Role(role),
                company_name=company,
                country=country,
                phone=phone,
                # New specialized fields (Request 1)
                expertise_area=expertise_area,
                job_title=job_title,
                bio=bio,
                website=website,
                # Initial trust_score (Request 2)
                trust_score_value=50  # Initial trust score
            )

            db.session.add(new_user)
            db.session.commit()

            # Create user profile
            from models.user import UserProfile
            if not new_user.profile:
                profile = UserProfile(user=new_user)
                db.session.add(profile)
                db.session.commit()

            flash("Registration successful! Please log in.")
            return redirect(url_for('users.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {e}")
            flash("An error occurred during registration.")
            return redirect(url_for('users.register'))

    # GET: Display smart registration form
    return render_template('users/register_dynamic.html', roles=Role)




# -------------------------------
# ورود
# -------------------------------
@users_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limiting برای جلوگیری از brute force
def login():

    if current_user.is_authenticated:
        return redirect(url_for('users.profile'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email, is_active=True).first()

        # بررسی قفل بودن حساب
        if user and user.locked_until:
            if datetime.utcnow() < user.locked_until:
                flash(f"❌ حساب شما تا {user.locked_until.strftime('%Y-%m-%d %H:%M')} به دلیل تلاش‌های ناموفق قفل است.")
                ActivityLog.log_activity(
                    user_id=user.id,
                    activity_type='login_blocked',
                    description='حساب کاربری به دلیل تلاش‌های ناموفق قفل است',
                    request=request,
                    success=False,
                    failure_reason='account_locked'
                )
                return render_template('users/login.html')
            else:
                # رفع قفل خودکار
                user.locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()

        if user and check_password_hash(user.password_hash, password):
            # ورود موفق - ریست کردن تلاش‌های ناموفق
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
                user.locked_until = None
                db.session.commit()
            
            # لاگ فعالیت ورود موفق
            ActivityLog.log_activity(
                user_id=user.id,
                activity_type='login',
                description='ورود موفق به سیستم',
                request=request,
                success=True
            )
            
            # ایجاد جلسه جدید
            session = LoginSession.create_session(
                user=user,
                request=request,
                remember_me=remember_me
            )
            session_token = session.session_token
            
            login_user(user, remember=remember_me)
            
            # ذخیره توکن جلسه در cookie
            response = redirect(url_for('users.profile'))
            response.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Lax')
            
            flash("✅ خوش آمدید!")
            return response
        else:
            # ورود ناموفق
            if user:
                user.failed_login_attempts += 1
                
                # قفل حساب پس از 5 تلاش ناموفق
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)  # 15 دقیقه قفل
                    db.session.commit()
                    
                    ActivityLog.log_activity(
                        user_id=user.id,
                        activity_type='account_locked',
                        description='حساب به دلیل 5 تلاش ناموفق قفل شد',
                        request=request,
                        success=False,
                        failure_reason='too_many_failed_attempts'
                    )
                    
                    flash("❌ حساب شما به دلیل تلاش‌های ناموفق زیاد به مدت 15 دقیقه قفل شد.")
                else:
                    db.session.commit()
                    
                    ActivityLog.log_activity(
                        user_id=user.id,
                        activity_type='login_failed',
                        description=f'تلاش ناموفق برای ورود ({user.failed_login_attempts}/5)',
                        request=request,
                        success=False,
                        failure_reason='invalid_password'
                    )
                    
                    remaining_attempts = 5 - user.failed_login_attempts
                    flash(f"❌ ایمیل یا رمز عبور نادرست است. {remaining_attempts} تلاش دیگر تا قفل شدن حساب.")
            else:
                # کاربر وجود ندارد - برای امنیت پیام کلی نمایش می‌دهیم
                flash("❌ ایمیل یا رمز عبور نادرست است.")
    
    support_user = User.query.filter_by(username='masoudkh', is_active=True).first()
    return render_template('users/login.html', support_user=support_user)



# -------------------------------
# ویرایش پروفایل پیشرفته
# -------------------------------
@users_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # اطلاعات پایه
        current_user.company_name = request.form.get('company', '').strip()
        current_user.country = request.form.get('country', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        
        # فیلدهای تخصصی جدید (درخواست ۴)
        current_user.expertise_area = request.form.get('expertise_area', '').strip()
        current_user.job_title = request.form.get('job_title', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.website = request.form.get('website', '').strip()
        
        # پردازش شبکه‌های اجتماعی (JSON format)
        social_links = {
            'linkedin': request.form.get('linkedin', '').strip(),
            'telegram': request.form.get('telegram', '').strip(),
            'whatsapp': request.form.get('whatsapp', '').strip()
        }
        # حذف مقادیر خالی
        social_links = {k: v for k, v in social_links.items() if v}
        current_user.social_links = json.dumps(social_links) if social_links else None
        
        # ✅ آپلود عکس پروفایل
        profile_file = request.files.get('profile_image')
        if profile_file and profile_file.filename != '':
            is_valid, error_msg = validate_file(profile_file, image_only=True)
            if not is_valid:
                flash(f"❌ {error_msg}", "error")
            else:
                upload_folder = current_app.config.get('PROFILE_UPLOAD_FOLDER', 'static/uploads/profiles')
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(profile_file.filename)
                unique_filename = f"{current_user.id}_{secrets.token_hex(8)}_{filename}"
                filepath = os.path.join(upload_folder, unique_filename)
                img = Image.open(profile_file)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                img.save(filepath, quality=85, optimize=True)
                if current_user.profile_image:
                    old_path = os.path.join(current_app.root_path, current_user.profile_image.lstrip('/'))
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old profile image: {e}")
                current_user.profile_image = f'/static/uploads/profiles/{unique_filename}'
                flash("✅ Profile picture updated successfully.", "success")

        db.session.commit()
        flash("✅ Profile updated successfully.", "success")
        return redirect(url_for('users.profile'))
    
    # GET: نمایش فرم ویرایش پروفایل
    return render_template('users/profile_edit.html', user=current_user)







# -------------------------------
# تنظیمات حساب کاربری
# -------------------------------
@users_bp.route('/account-settings')
@login_required
def account_settings():
    """نمایش صفحه تنظیمات حساب کاربری"""
    return render_template('users/account_settings.html', user=current_user)


# -------------------------------
# تغییر رمز عبور
# -------------------------------
@users_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """تغییر رمز عبور کاربر با اعتبارسنجی کامل"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # بررسی رمز عبور فعلی
    if not check_password_hash(current_user.password_hash, current_password):
        flash("❌ رمز عبور فعلی نادرست است.", "error")
        return redirect(url_for('users.account_settings'))
    
    # اعتبارسنجی رمز عبور جدید
    if len(new_password) < 8:
        flash("❌ رمز عبور جدید باید حداقل ۸ کاراکتر باشد.", "error")
        return redirect(url_for('users.account_settings'))
    
    # بررسی تطابق رمز جدید و تکرار آن
    if new_password != confirm_password:
        flash("❌ رمز عبور جدید و تکرار آن مطابقت ندارند.", "error")
        return redirect(url_for('users.account_settings'))
    
    # بررسی تکراری نبودن رمز عبور جدید با رمز قبلی
    if check_password_hash(current_user.password_hash, new_password):
        flash("⚠️ رمز عبور جدید نباید مشابه رمز عبور قبلی باشد.", "warning")
        return redirect(url_for('users.account_settings'))
    
    try:
        # به‌روزرسانی رمز عبور با هش کردن
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # لاگ عملیات برای امنیت
        current_app.logger.info(f"Password changed for user {current_user.id} ({current_user.email})")
        
        flash("✅ رمز عبور شما با موفقیت تغییر یافت.", "success")
        return redirect(url_for('users.account_settings'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing password for user {current_user.id}: {e}")
        flash("❌ خطایی در تغییر رمز عبور رخ داد. لطفاً مجدداً تلاش کنید.", "error")
        return redirect(url_for('users.account_settings'))


# -------------------------------
# حذف حساب کاربری
# -------------------------------
@users_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """حذف نرم حساب کاربری با تأیید دو مرحله‌ای"""
    
    # بررسی وجود چک‌باکس تأیید
    confirmation = request.form.get('confirmation_checkbox')
    if not confirmation:
        flash("⚠️ لطفاً برای حذف حساب، چک‌باکس تأیید را علامت بزنید.", "warning")
        return redirect(url_for('users.account_settings'))
    
    user_id = current_user.id
    user_email = current_user.email
    username = current_user.username
    
    try:
        # غیرفعال‌سازی حساب کاربری (soft delete)
        current_user.is_active = False
        
        # حذف توکن‌های فعال کاربر (در صورت وجود مدل Session/Token)
        # این بخش بستگی به پیاده‌سازی session management دارد
        # فعلاً logout انجام می‌دهیم
        logout_user()
        
        # لاگ عملیات برای امنیت
        current_app.logger.warning(
            f"Account deleted: User ID={user_id}, Email={user_email}, Username={username}"
        )
        
        # ارسال نوتیفیکیشن به ادمین (اختیاری)
        try:
            from models.notification import Notification
            admin_notification = Notification(
                user_id=None,  # نوتیفیکیشن سیستمی
                title="حذف حساب کاربری",
                message=f"حساب کاربری {username} ({user_email}) حذف شد.",
                category="admin_alert",
                is_read=False
            )
            db.session.add(admin_notification)
            db.session.commit()
        except Exception as notif_error:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin notification: {notif_error}")
        
        flash("🗑️ حساب کاربری شما با موفقیت حذف شد. از همکاری شما متشکریم.", "success")
        return redirect(url_for('users.register'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting account for user {user_id}: {e}")
        flash("❌ خطایی در حذف حساب رخ داد. لطفاً با پشتیبانی تماس بگیرید.", "error")
        return redirect(url_for('users.account_settings'))


# -------------------------------
# خروج
# -------------------------------
@users_bp.route('/logout')
@login_required
def logout():
    # لاگ فعالیت خروج
    ActivityLog.log_activity(
        user_id=current_user.id,
        activity_type='logout',
        description='خروج از سیستم',
        request=request,
        success=True
    )
    
    # باطل کردن جلسه فعلی
    session_token = request.cookies.get('session_token')
    if session_token:
        from hashlib import sha256
        hashed_token = sha256(session_token.encode()).hexdigest()
        login_session = LoginSession.query.filter_by(session_token=hashed_token).first()
        if login_session:
            login_session.revoke()
    
    logout_user()
    flash("👋 شما با موفقیت خارج شدید.")
    return redirect(url_for('users.login'))


@users_bp.route('/profile')
@login_required
def profile():
    """نمایش پروفایل کاربر با اطلاعات کامل و وضعیت مدارک"""

    if not current_user.is_active:
        logout_user()
        flash("❌ This account is inactive.")
        return redirect(url_for('users.login'))

    # محاسبه تعداد سفارش‌های در انتظار (فقط برای PRODUCER)
    pending_orders = 0
    if current_user.role == Role.PRODUCER:
        from models.order import OrderStatus,Order
        pending_orders = Order.query.filter_by(seller_id=current_user.id, status=OrderStatus.PENDING).count()

    # دریافت مدارک آپلود شده برای بررسی وضعیت تأیید
    verification_docs = json.loads(current_user.verification_documents) if current_user.verification_documents else []
    
    # تعیین وضعیت تأیید مدارک
    document_status = 'not_uploaded'  # not_uploaded, pending, approved, rejected
    if verification_docs:
        # اگر مدارک آپلود شده باشند، فرض می‌کنیم در حال بررسی هستند
        # در آینده می‌توان فیلد جداگانه برای وضعیت هر مدرک اضافه کرد
        document_status = 'pending'
        if current_user.is_verified:
            document_status = 'approved'
    
    # محاسبه وضعیت pending tasks
    pending_tasks = []
    if not current_user.is_verified and verification_docs:
        pending_tasks.append({
            'title': 'بررسی مدارک تأیید هویت',
            'description': 'مدارک شما در حال بررسی توسط ادمین است',
            'status': 'pending',
            'icon': 'document'
        })
    elif not current_user.is_verified and not verification_docs:
        pending_tasks.append({
            'title': 'آپلود مدارک تأیید هویت',
            'description': 'برای افزایش امتیاز اعتماد، مدارک خود را آپلود کنید',
            'status': 'action_required',
            'action_url': url_for('users.upload_documents'),
            'icon': 'upload'
        })
    
    # پروفایل کامل برای داشبورد هوشمند
    support_user = User.query.filter_by(username='support', is_active=True).first()

    if not support_user:
        support_user = User.query.filter_by(role=Role.PRODUCER, is_active=True).first()

    seller = User.query.filter_by(role=Role.PRODUCER, is_active=True).first()
    buyer = User.query.filter_by(role=Role.BUYER, is_active=True).first()
    broker = User.query.filter_by(role=Role.BROKER, is_premium=True, is_active=True).first()

    return render_template('users/dashboard.html', 
                          user=current_user,
                          support_user=support_user,
                          pending_orders=pending_orders,
                          seller=seller,
                          buyer=buyer,
                          broker=broker,
                          pending_tasks=pending_tasks,
                          verification_docs=verification_docs,
                          document_status=document_status)



from models.order import Order, OrderStatus


# routes/users/order_routes.py
from flask import flash, redirect, url_for, request, render_template
from flask_login import login_required, current_user
from models import db
from models.user import User, Role
from models.order import Order, OrderStatus
from . import users_bp
import requests

# Import fallback utility
from utils.fallback import get_data_with_fallback


@users_bp.route('/place_order', methods=['GET', 'POST'])
@login_required
def place_order():
    """
    ثبت سفارش با اعتبارسنجی کامل و امن
    """
    if request.method == 'POST':
        try:
            # دریافت و اعتبارسنجی ورودی
            product = request.form.get('product', '').strip()
            quantity_str = request.form.get('quantity', '').strip()
            price_str = request.form.get('price', '').strip()
            origin_port = request.form.get('origin_port', '').strip()
            destination_port = request.form.get('destination_port', '').strip()
            seller_id_str = request.form.get('seller_id', '').strip()
            notes = request.form.get('notes', '').strip()

            # ✅ اعتبارسنجی فیلدها
            if not product:
                flash("❌ Please enter the product name.")
                return redirect(url_for('users.place_order'))

            if not origin_port or not destination_port:
                flash("❌ Please select origin and destination.")
                return redirect(url_for('users.place_order'))

            # ✅ اعتبارسنجی کمیت و قیمت
            try:
                quantity = float(quantity_str)
                price = float(price_str)
                if quantity <= 0 or price <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                flash("❌ Invalid quantity or price.")
                return redirect(url_for('users.place_order'))

            # ✅ اعتبارسنجی فروشنده
            if not seller_id_str.isdigit():
                flash("❌ The seller is invalid.")
                return redirect(url_for('users.place_order'))

            seller_id = int(seller_id_str)
            seller = User.query.get(seller_id)

            if not seller:
                flash("❌ The desired seller was not found.")
                return redirect(url_for('users.place_order'))

            if seller.role != Role.PRODUCER:
                flash("❌ The selected user is not a producer.")
                return redirect(url_for('users.place_order'))

            # ✅ تعیین بروکر (فقط اگر کاربر ویژه باشد)
            broker_id = current_user.id if current_user.is_premium else None

            # ✅ ایجاد سفارش
            order = Order(
                product=product,
                quantity_tons=quantity,
                price_per_ton=price,
                origin_port=origin_port,
                destination_port=destination_port,
                notes=notes,
                buyer_id=current_user.id,
                seller_id=seller.id,
                broker_id=broker_id,
                status=OrderStatus.PENDING
            )
            order.calculate_total()

            # ✅ ارسال اعلان به فروشنده
            from models.notification import Notification
            notification = Notification(
                user_id=seller.id,
                message=f" You received a new order from {current_user.username} . (#{order.id})"
            )

            # ✅ افزودن و ذخیره در یک تراکنش واحد
            db.session.add(order)
            db.session.add(notification)
            db.session.commit()

            flash("✅ Order successfully placed.")
            return redirect(url_for('users.profile'))

        except Exception as e:
            db.session.rollback()  # ⚠️ بازگردانی تراکنش در صورت خطا
            print(f"❌ Error creating order: {e}")
            flash("❌ An error occurred while placing your order. Please try again.")
            return redirect(url_for('users.place_order'))

    # GET: نمایش فرم — فقط PRODUCERها
    sellers = User.query.filter_by(role=Role.PRODUCER, is_active=True).all()
    return render_template('users/place_order.html', sellers=sellers)


# -------------------------------
# نمایش سفارش‌های کاربر
# -------------------------------
@users_bp.route('/orders')
@login_required
def my_orders():
    orders = Order.query.filter(
        (Order.buyer_id == current_user.id) |
        (Order.seller_id == current_user.id) |
        (Order.broker_id == current_user.id)
    ).order_by(Order.created_at.desc()).all()
    return render_template('users/orders.html', orders=orders)


# -------------------------------
# نمایش سفارش‌های PRODUCER
# -------------------------------
@users_bp.route('/seller/orders')
@login_required
def seller_orders():
    if current_user.role != Role.PRODUCER:
        flash("❌ Only available to producers.")
        return redirect(url_for('users.profile'))

    orders = Order.query.filter_by(seller_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('users/seller_orders.html', orders=orders)


# -------------------------------
# تأیید سفارش توسط فروشنده
# -------------------------------
@users_bp.route('/order/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)

    if current_user.role != Role.PRODUCER or order.seller_id != current_user.id:
        flash("❌ Unauthorized access.")
        return redirect(url_for('users.profile'))

    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CONFIRMED
        # confirmed_at will be set automatically by the model's default

        # ارسال اعلان به خریدار
        from models.notification import Notification
        notification = Notification(
            user_id=order.buyer_id,
            message=f"Your order (#{order.id}) was confirmed by {current_user.username} ."
        )
        db.session.add(notification)
        db.session.commit()

        flash("✅ The order was confirmed and the notification was sent")
    else:
        flash("⚠️This order has already been approved or rejected.")

    return redirect(url_for('users.seller_orders'))


# -------------------------------
# رد سفارش توسط فروشنده
# -------------------------------
@users_bp.route('/order/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)

    if current_user.role != Role.PRODUCER or order.seller_id != current_user.id:
        flash("❌ Unauthorized access.")
        return redirect(url_for('users.profile'))

    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CANCELLED
        db.session.commit()
        flash(f"🗑️ Order #{order_id} rejected.")
    else:
        flash("⚠️ This order has already changed status.")

    return redirect(url_for('users.seller_orders'))


@users_bp.route('/notifications')
@login_required
def notifications():
    # خواندن همه اعلان‌ها
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

    # علامت‌گذاری به عنوان خوانده شده
    for n in notifs:
        if not n.is_read:
            n.is_read = True
    db.session.commit()

    return render_template('users/notifications.html', notifications=notifs)


@users_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    # ✅ فقط کاربران ویژه می‌تونن به لیست چت دسترسی داشته باشن و با کاربران دیگر چت کنن
    # اما کاربران غیر ویژه می‌تونن پیام‌های ادمین رو ببینن
    receiver_id = request.args.get('receiver_id', type=int)
    receiver = User.query.get(receiver_id) if receiver_id else None
    
    # بررسی اینکه آیا کاربر جاری غیر ویژه است و سعی دارد به چت دسترسی پیدا کند
    if not current_user.is_premium:
        # اگر کاربر غیر ویژه است، فقط می‌تواند پیام‌های ادمین را ببیند
        # نمی‌تواند به صورت فعال چت جدیدی شروع کند
        if request.method == 'POST':
            flash("❌ Limited access: Only special users can send messages.", "error")
            return redirect(url_for('users.profile'))
        
        # برای کاربران غیر ویژه، فقط نمایش پیام‌های ادمین مجاز است
        # لیست کاربران را خالی نگه می‌داریم
        users = []
        
        # اگر receiver مشخص شده، باید ادمین باشد
        if receiver and receiver.role != Role.ADMIN:
            flash("❌ Access denied: Non-special users can only view messages from admin.", "error")
            return redirect(url_for('users.profile'))
            
    else:
        # کاربران ویژه می‌تونن با همه کاربران ویژه چت کنن
        users = User.query.filter(
            User.id != current_user.id,
            User.is_premium == True
        ).all()

        # ✅ اگر گیرنده وجود نداشته باشه یا ویژه نباشه (برای کاربران عادی)
        if receiver and not receiver.is_premium:
            flash("❌ This user is not special and you cannot chat with him/her.", "error")
            receiver = None

    # ارسال پیام (فقط برای کاربران ویژه)
    if request.method == 'POST' and receiver and current_user.is_premium:
        content = request.form['content'].strip()
        if content:
            # ایجاد پیام
            msg = Message(
                sender_id=current_user.id,
                receiver_id=receiver.id,
                content=content
            )
            db.session.add(msg)
            db.session.commit()

            # ✅ ارسال اعلان به گیرنده
            notification = Notification(
                user_id=receiver.id,
                message=f"📩 You received a new message from {current_user.username} ."
            )
            db.session.add(notification)
            db.session.commit()

            flash("✉️ Message sent.")
        return redirect(url_for('users.chat', receiver_id=receiver.id))

    # دریافت پیام‌ها
    messages = []
    if receiver:
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver.id)) |
            ((Message.sender_id == receiver.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.asc()).all()

        # علامت‌گذاری پیام‌های دریافتی به عنوان خوانده شده
        for m in messages:
            if m.receiver_id == current_user.id and not m.is_read:
                m.is_read = True
        db.session.commit()

    return render_template('users/chat.html', users=users, receiver=receiver, messages=messages)


# ✅ مسیر جدید برای پشتیبانی - کاربران غیر ویژه می‌تونن پیام‌های ادمین رو اینجا ببینن و ارسال کنن
@users_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    """بخش پشتیبانی برای کاربران - مشاهده و ارسال پیام به ادمین"""
    # پیدا کردن کاربر ادمین
    admin_user = User.query.filter_by(role=Role.ADMIN, is_active=True).first()
    
    if not admin_user:
        flash("⚠️ No admin found to contact.", "warning")
        return redirect(url_for('users.profile'))
    
    # اگر درخواست POST است، کاربر می‌خواهد پیام ارسال کند
    if request.method == 'POST':
        content = request.form.get('message', '').strip()
        
        if not content:
            flash("❌ Please enter a message.", "error")
            return redirect(url_for('users.support'))
        
        # ایجاد پیام جدید از کاربر به ادمین
        message = Message(
            sender_id=current_user.id,
            receiver_id=admin_user.id,
            content=content
        )
        db.session.add(message)
        
        # ایجاد اعلان برای ادمین
        from models.notification import Notification
        notification = Notification(
            user_id=admin_user.id,
            message=f"📩 New support message from {current_user.username}"
        )
        db.session.add(notification)
        db.session.commit()
        
        flash("✅ Your message was sent to support.", "success")
        return redirect(url_for('users.support'))
    
    # دریافت پیام‌های بین کاربر جاری و ادمین
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == admin_user.id)) |
        ((Message.sender_id == admin_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    # علامت‌گذاری پیام‌های دریافتی به عنوان خوانده شده
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    
    return render_template('users/support.html', admin_user=admin_user, messages=messages)







from flask import g

@users_bp.app_context_processor
def inject_support_user():
    if current_user.is_authenticated:
        # مثلاً PRODUCER اول یا کاربر با username='support'
        support_user = User.query.filter_by(username='support', is_active=True).first()
        if not support_user:
            support_user = User.query.filter_by(role=Role.PRODUCER, is_active=True).first()
        return {'support_user': support_user}
    return {'support_user': None}


####################################
import requests
from flask import request
import json
from models import DataProvider
from functools import wraps

provider = DataProvider()
country_codes = provider.COUNTRY_CODES



@users_bp.route('/vessel_finder', methods=['GET', 'POST'])
@login_required
def vessel_finder():
    if not current_user.is_premium:
        flash("❌ Access is only allowed for special users.", "error")
        return redirect(url_for('users.profile'))

    # فقط در صورت POST و دریافت IMO
    if request.method == 'POST':
        imo = request.form.get('imo', '').strip()

        # اعتبارسنجی
        if not imo or not imo.isdigit() or len(imo) != 7:
            flash("❌ Please enter a valid 7-digit ID (IMO).", "error")
            return render_template('users/vessel_finder.html')

        url = f"https://api.searoutes.com/vessel/v2/{imo}/position"
        headers = {
            "X-API-Key": "zXlhor8hMV9fXyeZ3nero4aPpYAw39eU37KYP9ne",
            "Content-Type": "application/json"
        }

        def fetch_vessel_data():
            """Helper function to fetch data from API"""
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()

        # Use fallback mechanism
        data = get_data_with_fallback(url=url, fallback_query_func=None, timeout=10, headers=headers)

        # If network failed and no fallback data returned, show error
        if not data:
            flash("⚠️ Network unavailable. Showing demo data.", "warning")
            # Return demo/static data when offline
            return render_template(
                'users/vessel_finder.html',
                latitude=35.6892,  # Example: Tehran
                longitude=51.3890,
                imo=imo,
                mmsi="000000000",
                name="Demo Vessel (Offline Mode)",
                destination="Unknown",
                speed="0.0",
                date_arrival="N/A"
            )

        try:
            if not data:
                flash("❌ No data found for this ship.", "error")
                return render_template('users/vessel_finder.html')

            pos = data[0]['position']
            info = data[0]['info']

            return render_template(
                'users/vessel_finder.html',
                latitude=pos['geometry']['coordinates'][1],
                longitude=pos['geometry']['coordinates'][0],
                imo=info['imo'],
                mmsi=info['mmsi'],
                name=info['name'],
                destination=pos['properties'].get('destination', 'Uncertain'),
                speed=pos['properties'].get('speed', 'Uncertain'),
                date_arrival=pos['properties'].get('eta', 'Uncertain')
            )

        except requests.exceptions.Timeout:
            flash("❌ The request to the server was scheduled. Please try again.", "error")
        except requests.exceptions.RequestException as e:
            flash("❌ An error occurred with the ship tracking service.", "error")
        except (KeyError, IndexError) as e:
            flash("❌ The received data is invalid.", "error")

    # GET یا خطا: نمایش فرم
    return render_template('users/vessel_finder.html')
######################################TEST

# نمایش نقشه
@users_bp.route('/map')
@login_required
def show_map():
    if not current_user.is_premium:
        flash("❌ Only special users can access the map.")
        return redirect(url_for('users.profile'))
    
    # Fetch ports with fallback to local DB
    def get_local_ports():
        ports = Port.query.all()  # Limit for performance
        return [port.to_dict() for port in ports]
    
    # Try to fetch from external source (if you have one), otherwise use local DB
    # For now, we directly use local DB as primary source since ports are static
    ports_data = get_local_ports()
    
    # Ensure data structure is consistent
    if not ports_data:
        flash("⚠️ No port data available.", "warning")
        ports_data = []
    
    return render_template('users/map.html', ports=ports_data)


##############################################################test2

# routes/users/routes.py
from flask import jsonify


@users_bp.route('/api/ports', methods=['GET'])
@login_required
def get_ports():
    # فقط کاربران ویژه می‌تونن ببینن
    if not current_user.is_premium:
        return jsonify({'error': 'Restricted access: Special users only'}), 403

    # Fetch ports from local DB (always available, no external dependency)
    try:
        ports = Port.query.all()  # Limit for API performance
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'country': p.country,
            'location': [p.latitude, p.longitude]
        } for p in ports])
    except Exception as e:
        # Fallback to empty list if DB error
        return jsonify([]), 200


@users_bp.route('/add_port', methods=['POST'])
@login_required
def add_port():
    if current_user.role != Role.PRODUCER:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    port = Port(
        name=data['name'],
        country=data['country'],
        latitude=data['latitude'],
        longitude=data['longitude']
    )
    db.session.add(port)
    db.session.commit()
    return jsonify({'message': 'Port added.', 'port': port.to_dict()})


@users_bp.route('/update_port/<port_id>', methods=['PUT'])
@login_required
def update_port(port_id):
    if current_user.role != Role.PRODUCER:
        return jsonify({'error': 'Access denied'}), 403

    # ✅ چک کردن اینکه port_id عددی باشه
    if not port_id.isdigit():
        return jsonify({'error': 'The port ID must be a positive number.'}), 400

    port_id = int(port_id)

    port = Port.query.get_or_404(port_id)
    data = request.get_json()

    port.name = data['name']
    port.country = data['country']
    port.latitude = data['latitude']
    port.longitude = data['longitude']

    db.session.commit()
    return jsonify({'message': 'Port successfully updated.'})


@users_bp.route('/delete_port/<port_id>', methods=['DELETE'])
@login_required
def delete_port(port_id):
    if current_user.role != Role.PRODUCER:
        return jsonify({'error': 'Access denied'}), 403
    if not port_id.isdigit():
        return jsonify({'error': 'The port ID must be a positive number.'}), 400

    port_id = int(port_id)
    port = Port.query.get_or_404(port_id)
    db.session.delete(port)
    db.session.commit()
    return jsonify({'message': 'The port was removed.'})

# @users_bp.route('/test')
# def test():
#     return "✅ مسیر /users/test کار می‌کنه!"

####################################################################

import os
from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.premium_request import PremiumRequest

# مسیر اصلی ارتقاء
@users_bp.route('/upgrade_to_premium')
@login_required
def upgrade_to_premium():
    # آخرین درخواست کاربر
    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()
    # دریافت تمام درخواست‌ها برای نمایش تاریخچه
    requests = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(
        PremiumRequest.submitted_at.desc()).all()

    if req:
        if req.status == 'approved':
            flash("✅ You have already become a special user.")
            return redirect(url_for('users.profile'))
        elif req.status == 'pending':
            flash("⚠️ Your request is being reviewed.")
            return redirect(url_for('users.payment_confirmation',now=datetime.now()))

    # ارسال `req` به تمپلیت
    return render_template('users/upgrade_premium.html', req=req, requests=requests)

# شروع فرآیند (ایجاد درخواست جدید)
@users_bp.route('/start_upgrade', methods=['POST'])
@login_required
def start_upgrade():
    # همیشه یک درخواست جدید ایجاد می‌کنیم
    req = PremiumRequest(user_id=current_user.id)
    db.session.add(req)
    db.session.commit()

    flash("The upgrade process has started. Please verify your mobile number.")
    return redirect(url_for('users.verify_phone'))

# آپلود مدارک برای Premium
@users_bp.route('/upload_documents', methods=['GET', 'POST'])
@login_required
def upload_documents():
    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()

    # if not req or not req.email_verified:
    #     flash("لطفاً ابتدا ایمیل خود را تأیید کنید.", "error")
    #     return redirect(url_for('users.verify_email'))

    # if req.docs_verified:
    #     flash("مدارک شما قبلاً تأیید شده است.", "success")
    #     return redirect(url_for('users.make_payment'))

    upload_folder = 'static/uploads/documents/'
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == 'POST':
        files_uploaded = False

        # پردازش پاسپورت
        passport_file = request.files.get('passport_file')
        if passport_file and passport_file.filename != '':
            is_valid, error_msg = validate_file(passport_file)
            if not is_valid:
                flash(f"❌ {error_msg}", "error")
                return redirect(url_for('users.upload_documents'))

            filename = secure_filename(f"passport_{current_user.id}_{passport_file.filename}")
            passport_file.save(os.path.join(upload_folder, filename))
            req.passport_file = filename
            files_uploaded = True

        # پردازش لایسنس
        license_file = request.files.get('license_file')
        if license_file and license_file.filename != '':
            is_valid, error_msg = validate_file(license_file)
            if not is_valid:
                flash(f"❌ {error_msg}", "error")
                return redirect(url_for('users.upload_documents'))

            filename = secure_filename(f"license_{current_user.id}_{license_file.filename}")
            license_file.save(os.path.join(upload_folder, filename))
            req.license_file = filename
            files_uploaded = True

        if files_uploaded:
            req.docs_verified = True
            db.session.commit()

            flash("✅ مدارک با موفقیت آپلود شدند.", "success")
            return redirect(url_for('users.make_payment'))
        else:
            flash("❌ هیچ فایلی برای آپلود دریافت نشد. لطفاً فایل‌ها را انتخاب و مجدداً تلاش کنید.", "error")

    return render_template('users/upload_documents.html', req=req)

# پرداخت و آپلود رسید
@users_bp.route('/make_payment', methods=['GET', 'POST'])
@login_required
def make_payment():
    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()


    if not req or not req.docs_verified:
        return redirect(url_for('users.upload_documents'))

    if req.payment_verified:
        return redirect(url_for('users.payment_confirmation',now=datetime.now()))


    if request.method == 'POST':
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file.filename != '':
                filename = secure_filename(f"receipt_{current_user.id}_{file.filename}")
                file.save(os.path.join('static/uploads/', filename))
                req.payment_receipt = filename

                req.status = 'pending'
                req.payment_verified = True
                db.session.commit()
                flash("Payment receipt received. Reviewing...")
                # ارسال اعلان به ادمین
                notify_admin_of_new_request(req)
                return redirect(url_for('users.payment_confirmation',now=datetime.now()))

    return render_template('users/make_payment.html', req=req)

# تأیید نهایی
@users_bp.route('/payment_confirmation')
@login_required
def payment_confirmation():
    return render_template('users/payment_confirmation.html',now=datetime.now())

# --- تابع کمکی: اعلان به ادمین ---
def notify_admin_of_new_request(req):
    """Send email notification to admins when a new premium request is submitted."""
    from flask_mail import Message
    from extensions import mail
    from flask import current_app
    
    try:
        admins = User.query.filter_by(role=Role.ADMIN, is_active=True).all()
        emails = [a.email for a in admins if a.email]

        if emails:
            msg = Message(
                subject="🔔 New request for promotion to special user",
                recipients=emails,
                body=f"User {req.user.username} has submitted a new request for premium access."
            )
            mail.send(msg)
            current_app.logger.info(f"Notification sent to {len(emails)} admin(s) for user {req.user.username}")
    except Exception as e:
        current_app.logger.error(f"Error sending admin notification: {e}")
        # Don't raise exception - this is a non-critical operation