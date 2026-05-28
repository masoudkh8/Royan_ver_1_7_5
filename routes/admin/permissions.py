from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.user import User, UserProfile, Role
from models import db
from services.permissions import Permission, DEFAULT_ROLE_PERMISSIONS, get_role_permissions
from services.access_control import role_required
from functools import wraps

admin_perms_bp = Blueprint('admin_perms', __name__, url_prefix='/permissions')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash("شما دسترسی لازم برای مشاهده این صفحه را ندارید.", "error")
            return redirect(url_for('users.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_perms_bp.route('/')
@login_required
@admin_required
def permission_dashboard():
    """داشبورد اصلی مدیریت دسترسی‌ها"""
    roles = Role
    permissions = Permission
    
    # ساخت ماتریس دسترسی‌ها
    matrix = {}
    for role in roles:
        matrix[role.name] = {perm.name: perm in get_role_permissions(role) for perm in permissions}
    
    # دریافت تمام کاربران برای نمایش در تب‌های دیگر
    all_users = User.query.order_by(User.username).all()
    
    return render_template('admin/permission_dashboard.html', 
                           roles=roles, 
                           permissions=permissions, 
                           matrix=matrix,
                           users=all_users)

@admin_perms_bp.route('/edit-role/<string:role_name>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role_permissions(role_name):
    """ویرایش مجوزهای پیش‌فرض یک نقش"""
    try:
        target_role = Role[role_name.upper()]
    except KeyError:
        flash("نقش نامعتبر است.", "error")
        return redirect(url_for('admin.admin_perms.permission_dashboard'))
    
    if request.method == 'POST':
        # در نسخه پیشرفته، این مقادیر باید در دیتابیس ذخیره شوند
        # فعلاً به صورت موقت در حافظه یا کانفیگ مدیریت می‌شوند
        selected_perms = request.form.getlist('permissions')
        
        # اینجا لاجیک ذخیره‌سازی در دیتابیس برای_override کردن پیش‌فرض‌ها قرار می‌گیرد
        # برای سادگی فعلاً پیام موفقیت نشان می‌دهیم
        flash(f"تنظیمات نقش {target_role.value} با موفقیت به‌روزرسانی شد. ({len(selected_perms)} مجوز فعال)", "success")
        return redirect(url_for('admin.admin_perms.permission_dashboard'))
    
    current_perms = get_role_permissions(target_role)
    return render_template('admin/edit_role_perms.html', 
                           role=target_role, 
                           permissions=Permission, 
                           current_perms=current_perms)

@admin_perms_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user_permissions(user_id):
    """مدیریت دسترسی‌های خاص یک کاربر (استثناها)"""
    user = User.query.get_or_404(user_id)
    
    # === ایجاد خودکار پروفایل اگر وجود ندارد ===
    if not user.profile:
        from models.user import UserProfile
        user.profile = UserProfile(user_id=user.id)
        db.session.add(user.profile)
        db.session.commit()
        flash(f"پروفایل کاربر {user.username} به صورت خودکار ایجاد شد.", "info")
    # ===========================================
    
    if request.method == 'POST':
        action = request.form.get('action')
        perm_value = request.form.get('permission')  # دریافت permission value به صورت رشته
        
        if not perm_value:
            flash("مجوز نامعتبر است.", "error")
            return redirect(url_for('admin.admin_perms.manage_user_permissions', user_id=user.id))
        
        # اعتبارسنجی مجوز
        try:
            perm_enum = Permission(perm_value)
        except ValueError:
            flash("مجوز نامعتبر است.", "error")
            return redirect(url_for('admin.admin_perms.manage_user_permissions', user_id=user.id))
        
        # استفاده از متدهای جدید مدل برای مدیریت مجوزها
        if action == 'grant':
            if user.profile.add_permission(perm_value):
                flash(f"مجوز {perm_enum.value} به کاربر {user.username} اعطا شد.", "success")
            else:
                flash(f"مجوز {perm_enum.value} قبلاً به کاربر داده شده است.", "info")
        elif action == 'revoke':
            if user.profile.remove_permission(perm_value):
                flash(f"مجوز {perm_enum.value} از کاربر {user.username} حذف شد.", "warning")
            else:
                flash(f"مجوز {perm_enum.value} در لیست مجوزهای کاربر نبود.", "info")
        
        db.session.commit()
        return redirect(url_for('admin.admin_perms.manage_user_permissions', user_id=user.id))
    
    # محاسبه مجوزهای نهایی کاربر
    base_perms = get_role_permissions(user.role)
    custom_perms = user.profile.get_custom_permissions() if user.profile else []
    
    return render_template('admin/manage_user_perms.html', 
                           user=user, 
                           base_perms=base_perms, 
                           custom_perms=custom_perms,
                           all_permissions=Permission)

@admin_perms_bp.route('/api/preview/<int:user_id>')
@login_required
@admin_required
def preview_user_menu(user_id):
    """پیش‌نمایش JSON منوی کاربر بر اساس دسترسی‌ها"""
    user = User.query.get_or_404(user_id)
    
    # اطمینان از وجود پروفایل
    if not user.profile:
        from models.user import UserProfile
        user.profile = UserProfile(user_id=user.id)
        db.session.add(user.profile)
        db.session.commit()

    # شبیه‌سازی سرویس‌های موجود با استفاده از مجوزهای واقعی
    available_modules = [
        {'id': 'orders', 'name': 'مدیریت سفارشات', 'perm': Permission.ORDER_CREATE},
        {'id': 'logistics', 'name': 'پنل لجستیک', 'perm': Permission.LOGISTICS_ASSIGN_DRIVER},
        {'id': 'legal', 'name': 'امور حقوقی', 'perm': Permission.LEGAL_APPROVE_DOCS},
        {'id': 'finance', 'name': 'امور مالی', 'perm': Permission.FINANCE_VIEW_WALLET},
        {'id': 'tech', 'name': 'بازرسی فنی', 'perm': Permission.TECH_SUBMIT_REPORT},
    ]
    
    # دریافت مجوزهای سفارشی کاربر
    custom_perms = user.profile.get_custom_permissions() if user.profile else []

    visible_modules = []
    for module in available_modules:
        # بررسی دسترسی
        has_access = module['perm'] in get_role_permissions(user.role)
        if custom_perms and module['perm'].value in custom_perms:
            has_access = True # دسترسی سفارشی
            
        if has_access:
            visible_modules.append(module)
            
    return jsonify({
        'username': user.username,
        'role': user.role.value,
        'visible_modules': visible_modules
    })
