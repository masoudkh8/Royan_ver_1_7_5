# routes/admin/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user

from models import db, Notification, Message
from models.user import User, Role
from models.premium_request import PremiumRequest

from datetime import datetime
import pytz
tehran_tz = pytz.timezone('Asia/Tehran')

from functools import wraps
from flask import request, flash, redirect, url_for, render_template
from flask_login import login_user
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import admin_bp



@admin_bp.before_request
def make_session_permanent():
    """Make sessions permanent so they expire after PERMANENT_SESSION_LIFETIME"""
    session.permanent = True


# ---------------------------------------
# TODO: Translate -  Decorator: فقط ادمین Access داشته باشه
# ---------------------------------------


@admin_bp.route('/admin')
def admin_index():
    return redirect(url_for('admin.login'))

def admin_required(f):
    @wraps(f)  # TODO: Translate -  ✅ این خط مشکل رو حل می‌کنه
    def decorated_function(*args, **kwargs):
        # TODO: Translate -  ✅ اول چک کن User واReject شده باشد
        if not current_user.is_authenticated:
            flash("❌ Please log in first.")
            return redirect(url_for('users.login'))

        if  current_user.role != Role.ADMIN:
            flash("❌ Access denied: Only admin can access this page.", "error")
            return redirect(url_for('users.profile'))
        return f(*args, **kwargs)

    return decorated_function


# ---------------------------------------
# TODO: Translate -  داشبوReject ادمین
# ---------------------------------------
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """TODO: Translate - داشبوReject ادمین با View آمار و نوتیفیکیشن‌های جدید"""
    from models.auth import ActivityLog
    
    total_users = User.query.count()
    premium_requests = PremiumRequest.query.count()
    pending_requests = PremiumRequest.query.filter_by(status='pending').count()
    
    # TODO: Translate -  شمارش مدارک Upload شده برای Check (Userانی که مدارک دارند اما هنوز Confirm نشده‌اند)
    users_with_pending_docs = User.query.filter(
        User.verification_documents != None,
        User.verification_documents != '[]',
        User.is_verified == False
    ).count()
    
    # TODO: Translate -  دریافت نوتیفیکیشن‌های خوانده‌نشده ادمین
    from models.notification import Notification
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    # ✅ Fetch recent activity logs for admin dashboard
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           premium_requests=premium_requests,
                           pending_requests=pending_requests,
                           users_with_pending_docs=users_with_pending_docs,
                           unread_notifications=unread_notifications,
                           unread_count=unread_count,
                           recent_activities=recent_activities)


# ---------------------------------------
# TODO: Translate -  مدیریت Userان
# ---------------------------------------

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status_filter = request.args.get('status', 'active')

    query = User.query

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    users = query.order_by(User.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # TODO: Translate -  ✅ محاسبه تعداد در بک‌اند
    total_active = User.query.filter_by(is_active=True).count()
    total_inactive = User.query.filter_by(is_active=False).count()

    return render_template(
        'admin/manage_users.html',
        users=users,
        status_filter=status_filter,
        total_active=total_active,
        total_inactive=total_inactive
    )
# ---------------------------------------
# TODO: Translate -  تغییر Role User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if not Role.has_value(new_role):
        flash("❌ The role is invalid.", "error")
    else:
        user.role = Role(new_role)
        # print(new_role)
        if new_role=="admin":
            user.is_premium=True
            from models.user import MembershipTier
            user.membership_tier = MembershipTier.VERIFIED
            user.is_kyc_verified = True
            user.premium_since = datetime.now(tehran_tz)
        db.session.commit()
        flash(f"✅ User role {user.username} changed to '{new_role}' .", "success")
    return redirect(url_for('admin.manage_users'))


# ---------------------------------------
# TODO: Translate -  Request‌های ارتقاء به User ویژه
# ---------------------------------------
@admin_bp.route('/premium_requests')
@admin_required
def premium_requests():
    status_filter = request.args.get('status', 'all')
    query = PremiumRequest.query.order_by(PremiumRequest.submitted_at.desc())

    if status_filter == 'pending':
        query = query.filter_by(status='pending')
    elif status_filter == 'approved':
        query = query.filter_by(status='approved')
    elif status_filter == 'rejected':
        query = query.filter_by(status='rejected')

    requests = query.all()
    return render_template('admin/premium_requests.html', requests=requests, status_filter=status_filter)


# ---------------------------------------
# TODO: Translate -  Confirm یا Reject Request ارتقاء (یکپارچه‌سازی approve و reject)
# ---------------------------------------
@admin_bp.route('/premium_request/<int:req_id>/review', methods=['POST'])
@admin_required
def review_premium_request(req_id):
    req = PremiumRequest.query.get_or_404(req_id)
    action = request.form.get('action')
    
    if action == 'approve':
        req.status = 'approved'
        req.user.is_premium = True
        # TODO: Translate -  ارتقای لایه عضویت به VERIFIED (لایه ۲)
        from models.user import MembershipTier
        req.user.membership_tier = MembershipTier.VERIFIED
        #  Confirm KYC
        req.user.is_kyc_verified = True
        # TODO: Translate -  افزایش Score Trust (Trust Score)
        req.user.trust_score_value = min(100, req.user.trust_score_value + 20)
        # TODO: Translate -  ثبت Time پریمیوم شدن
        req.user.premium_since = datetime.now(tehran_tz)
        
        # TODO: Translate -  Save مدارک در Field verification_documents
        import json
        docs = {
            'passport': req.passport_file,
            'license': req.license_file,
            'payment_receipt': req.payment_receipt,
            'verified_at': datetime.now(tehran_tz).isoformat()
        }
        req.user.verification_documents = json.dumps(docs)
        
        db.session.commit()
        flash(f"✅ User '{req.user.username}' successfully promoted to Premium Level 1 (Verified). Trust Score increased by 20 points!", "success")
    elif action == 'reject':
        req.status = 'rejected'
        db.session.commit()
        flash(f"❌ Upgrade Request for '{req.user.username}' rejected.", "warning")
    else:
        flash("⚠️ Invalid action.", "error")
        return redirect(url_for('admin.view_premium_request', req_id=req_id))
    
    db.session.commit()
    return redirect(url_for('admin.premium_requests'))


# ---------------------------------------
# TODO: Translate -  Confirm Request ارتقاء (قدیمی - برای سازگاری)
# ---------------------------------------
@admin_bp.route('/approve_premium/<int:req_id>', methods=['POST'])
@admin_required
def approve_premium(req_id):
    req = PremiumRequest.query.get_or_404(req_id)
    req.status = 'approved'
    req.user.is_premium = True
    # TODO: Translate -  ارتقای لایه عضویت به VERIFIED (لایه ۲)
    from models.user import MembershipTier
    req.user.membership_tier = MembershipTier.VERIFIED
    #  Confirm KYC
    req.user.is_kyc_verified = True
    # TODO: Translate -  ثبت Time پریمیوم شدن
    req.user.premium_since = datetime.now(tehran_tz)
    db.session.commit()

    flash(f"✅ User '{req.user.username}' Successfully promoted to special user.", "success")
    return redirect(url_for('admin.premium_requests'))


# ---------------------------------------
# TODO: Translate -  Reject Request ارتقاء (قدیمی - برای سازگاری)
# ---------------------------------------
@admin_bp.route('/reject_premium/<int:req_id>', methods=['POST'])
@admin_required
def reject_premium(req_id):
    req = PremiumRequest.query.get_or_404(req_id)
    req.status = 'rejected'
    db.session.commit()

    flash(f"❌ Upgrade Request for '{req.user.username}' rejected.", "warning")
    return redirect(url_for('admin.premium_requests'))


# ---------------------------------------
# TODO: Translate -  مشاهده جزئیات Request
# ---------------------------------------
@admin_bp.route('/premium_request/<int:req_id>')
@admin_required
def view_premium_request(req_id):
    req = PremiumRequest.query.get_or_404(req_id)
    return render_template('admin/view_premium_request.html', req=req)


# ---------------------------------------
# TODO: Translate -  مشاهده مدارک User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/documents')
@admin_required
def view_user_documents(user_id):
    user = User.query.get_or_404(user_id)
    
    # TODO: Translate -  دریافت مدارک از Field verification_documents (JSON format)
    import json
    documents = json.loads(user.verification_documents) if user.verification_documents else []
    
    return render_template('admin/view_user_documents.html', user=user, documents=documents)


# ---------------------------------------
# TODO: Translate -  مشاهده همه مدارک Userان برای Check
# ---------------------------------------
@admin_bp.route('/documents')
@admin_required
def view_all_documents():
    """TODO: Translate - View List تمام Userانی که مدارک Upload کRejectه‌اند"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    status_filter = request.args.get('status', 'pending')  # pending, approved, rejected, all
    
    query = User.query.filter(
        User.verification_documents != None,
        User.verification_documents != '[]'
    )
    
    if status_filter == 'pending':
        query = query.filter_by(is_verified=False)
    elif status_filter == 'approved':
        query = query.filter_by(is_verified=True)
    
    users_with_docs = query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # TODO: Translate -  آمار
    total_pending = User.query.filter(
        User.verification_documents != None,
        User.verification_documents != '[]',
        User.is_verified == False
    ).count()
    
    total_approved = User.query.filter(
        User.verification_documents != None,
        User.verification_documents != '[]',
        User.is_verified == True
    ).count()
    
    return render_template('admin/view_all_documents.html', 
                          users=users_with_docs,
                          total_pending=total_pending,
                          total_approved=total_approved,
                          current_status=status_filter)


# ---------------------------------------
# TODO: Translate -  Confirm مدارک User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/verify_documents', methods=['POST'])
@admin_required
def verify_user_documents(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    user.is_kyc_verified = True
    
    # TODO: Translate -  اگر User مدارک Complete داReject، لایه عضویت را ارتقا بده
    from models.user import MembershipTier
    if user.verification_documents and user.verification_documents != '[]':
        user.membership_tier = MembershipTier.VERIFIED
    
    # TODO: Translate -  Create نوتیفیکیشن برای User
    from models.notification import Notification
    notification = Notification(
        user_id=user.id,
        notification_type='system',
        actor_id=current_user.id,
        related_id=user.id,
        related_type='document_verified',
        title='✅ مدارک شما تأیید شد',
        message=f'مدارک تأیید هویت شما با موفقیت تأیید شد. امتیاز اعتماد شما افزایش یافت.'
    )
    db.session.add(notification)
    
    # TODO: Translate -  افزایش TrustScore
    if user.trust_score:
        user.trust_score_value = min(100, user.trust_score_value + 20)
    
    db.session.commit()
    flash(f"✅ مدارک کاربر '{user.username}' با موفقیت تأیید شد.", "success")
    return redirect(url_for('admin.view_user_documents', user_id=user_id))


# ---------------------------------------
# TODO: Translate -  Reject مدارک User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/reject_documents', methods=['POST'])
@admin_required
def reject_user_documents(user_id):
    user = User.query.get_or_404(user_id)
    # TODO: Translate -  می‌توانیم مدارک را پاک کنیم یا فقط Status را تغییر دهیم
    # TODO: Translate -  در اینجا فقط Status را به False تغییر می‌دهیم
    user.is_verified = False
    
    # TODO: Translate -  Create نوتیفیکیشن برای User
    from models.notification import Notification
    notification = Notification(
        user_id=user.id,
        notification_type='system',
        actor_id=current_user.id,
        related_id=user.id,
        related_type='document_rejected',
        title='⚠️ مدارک شما رد شد',
        message=f'مدارک تأیید هویت شما مورد تأیید قرار نگرفت. لطفاً مدارک صحیح را آپلود کنید.'
    )
    db.session.add(notification)
    
    db.session.commit()
    flash(f"⚠️ مدارک کاربر '{user.username}' رد شد.", "warning")
    return redirect(url_for('admin.view_user_documents', user_id=user_id))


# ---------------------------------------
# TODO: Translate -  Delete User (با احتیاط)
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    Notification.query.filter_by(user_id=user_id).delete()
    if current_user.id == user_id:
        flash("❌ You cannot delete yourself.", "error")
        return redirect(url_for('admin.manage_users'))

    user = User.query.get_or_404(user_id)
    username = user.username

    # TODO: Translate -  Delete Request ارتقاء اگر وجود داشت
    req = PremiumRequest.query.filter_by(user_id=user.id).first()
    if req:
        db.session.delete(req)

    user.is_active = False
    # db.session.delete(user)
    db.session.commit()

    flash(f" User✅{username} deleted successfully." ,"success")
    return redirect(url_for('admin.manage_users'))



# ---------------------------------------
# TODO: Translate -  غیرActive‌سازی User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    if current_user.id == user_id:
        flash("❌ You cannot deactivate yourself.")
        return redirect(url_for('admin.manage_users'))

    user = User.query.get_or_404(user_id)
    if user.role == Role.ADMIN:
        flash("❌ You cannot deactivate another admin.")
        return redirect(url_for('admin.manage_users'))

    user.is_active = False
    db.session.commit()
    flash(f"✅ User'{user.username}' has been disabled.")
    return redirect(url_for('admin.manage_users', status=request.args.get('status', 'active')))


# ---------------------------------------
# TODO: Translate -  Active‌سازی User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f"✅ User'{user.username}' activated.")
    return redirect(url_for('admin.manage_users', status=request.args.get('status', 'active')))


# ---------------------------------------
# TODO: Translate -  تغییر Status ویژه (Premium) User
# ---------------------------------------
@admin_bp.route('/user/<int:user_id>/toggle_premium', methods=['POST'])
@admin_required
def toggle_premium(user_id):
    if current_user.id == user_id:
        flash("❌ You cannot change your own special status.", "error")
        return redirect(url_for('admin.manage_users'))

    user = User.query.get_or_404(user_id)
    user.is_premium = not user.is_premium
    
    # TODO: Translate -  اگر User پریمیوم شد، لایه عضویت را ارتقا بده
    if user.is_premium:
        from models.user import MembershipTier
        user.membership_tier = MembershipTier.VERIFIED
        user.is_kyc_verified = True
        user.premium_since = datetime.now(tehran_tz)
    
    db.session.commit()
    
    if user.is_premium:
        flash(f"✅ User '{user.username}' is now a special user.", "success")
    else:
        flash(f"⚠️ Special status removed from user '{user.username}'.", "warning")
    
    return redirect(url_for('admin.manage_users'))


# ---------------------------------------
# TODO: Translate -  Chat ادمین با Userان
# ---------------------------------------
@admin_bp.route('/chat')
@admin_required
def admin_chat_list():
    """TODO: Translate - List Userان برای Chat - View همه Userان Active (ویژه و غیر ویژه)"""
    users = User.query.filter(
        User.id != current_user.id,
        User.is_active == True
    ).order_by(User.username.asc()).all()
    return render_template('admin/chat.html', users=users)


@admin_bp.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_chat_with_user(user_id):
    """TODO: Translate - Chat ادمین با یک User خاص"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("❌ You cannot chat with yourself.", "error")
        return redirect(url_for('admin.admin_chat_list'))
    
    # TODO: Translate -  دریافت Message‌های بین ادمین و این User
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) |
        ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # TODO: Translate -  علامت‌گذاری Message‌های دریافتی به عنوان خوانده شده
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    
    # TODO: Translate -  ارسال Message
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            msg = Message(
                sender_id=current_user.id,
                receiver_id=user.id,
                content=content
            )
            db.session.add(msg)
            
            # TODO: Translate -  Create Notification برای User
            notification = Notification(
                user_id=user.id,
                message=f"📩 You received a new message from Admin."
            )
            db.session.add(notification)
            db.session.commit()
            
            flash("✅ Message sent to user.", "success")
            return redirect(url_for('admin.admin_chat_with_user', user_id=user.id))
    
    return render_template('admin/chat_with_user.html', user=user, messages=messages)


#  Page Login
@admin_bp.route('/login')
def login():
    # TODO: Translate -  اگر اولین ادمین وجود نداReject، به Page ساخت ادمین هدایت کن
    admin_exists = User.query.filter_by(role=Role.ADMIN).first()
    if not admin_exists:
        return redirect(url_for('admin.create_first_admin'))
    return render_template('admin/login.html', current_year=datetime.now().year)

# TODO: Translate -  پRejectازش Login
@admin_bp.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email, is_active=True).first()

    if user and check_password_hash(user.password_hash, password):
        if user.role ==  Role.ADMIN:
            login_user(user)
            flash("✅ Welcome, admin.!", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            print(user.role)
            print(user)
            flash("❌ Access denied: Only admin can log in.", "error")
    else:
        flash("❌ The email or password is incorrect.", "error")

    return redirect(url_for('admin.login'))


# ---------------------------------------
# TODO: Translate -  ساخت اولین ادمین (فقط Timeی که هیچ ادمینی وجود نداReject)
# ---------------------------------------
@admin_bp.route('/create-first-admin', methods=['GET', 'POST'])
def create_first_admin():
    # TODO: Translate -  Check اینکه آیا ادمینی وجود داReject یا خیر
    admin_exists = User.query.filter_by(role=Role.ADMIN).first()
    
    if admin_exists:
        flash("⚠️ Admin already exists. Please log in.", "warning")
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # TODO: Translate -  Creditسنجی
        errors = []
        
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        
        if not email or '@' not in email:
            errors.append("Please enter a valid email address.")
        
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        
        if password != confirm_password:
            errors.append("Passwords do not match.")
        
        # TODO: Translate -  Check تکراری بودن ایمیل
        if User.query.filter_by(email=email).first():
            errors.append("This email is already registered.")
        
        # TODO: Translate -  Check تکراری بودن نام Userی
        if User.query.filter_by(username=username).first():
            errors.append("This username is already taken.")
        
        if errors:
            for error in errors:
                flash(f"❌ {error}", "error")
            return render_template('admin/create_first_admin.html', 
                                 username=username, 
                                 email=email,
                                 current_year=datetime.now().year)
        
        # TODO: Translate -  ساخت User ادمین
        from werkzeug.security import generate_password_hash
        from models.user import MembershipTier
        
        admin_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=Role.ADMIN,
            is_active=True,
            is_verified=True,
            is_kyc_verified=True,
            is_premium=True,
            membership_tier=MembershipTier.ELITE,
            trust_score_value=100,
            premium_since=datetime.now(tehran_tz)
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        # TODO: Translate -  لاگ Activeیت
        from models.auth import ActivityLog
        activity = ActivityLog(
            activity_type='first_admin_created',
            description='First admin account created automatically',
            request=request
        )
        db.session.add(activity)
        db.session.commit()
        
        flash("✅ First admin account created successfully! Please log in.", "success")
        return redirect(url_for('admin.login'))
    
    return render_template('admin/create_first_admin.html', 
                         username='', 
                         email='',
                         current_year=datetime.now().year)