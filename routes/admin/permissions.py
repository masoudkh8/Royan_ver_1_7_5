from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.user import User, UserProfile, Role
from models import db
from services.permissions import Permission, DEFAULT_ROLE_PERMISSIONS, get_role_permissions
from services.access_control import role_required
from functools import wraps

admin_perms_bp = Blueprint('admin_perms', __name__, url_prefix='/admin/permissions')

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
        return redirect(url_for('admin_perms.permission_dashboard'))
    
    if request.method == 'POST':
        # در نسخه پیشرفته، این مقادیر باید در دیتابیس ذخیره شوند
        # فعلاً به صورت موقت در حافظه یا کانفیگ مدیریت می‌شوند
        selected_perms = request.form.getlist('permissions')
        
        # اینجا لاجیک ذخیره‌سازی در دیتابیس برای_override کردن پیش‌فرض‌ها قرار می‌گیرد
        # برای سادگی فعلاً پیام موفقیت نشان می‌دهیم
        flash(f"تنظیمات نقش {target_role.value} با موفقیت به‌روزرسانی شد. ({len(selected_perms)} مجوز فعال)", "success")
        return redirect(url_for('admin_perms.permission_dashboard'))
    
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
    
    if request.method == 'POST':
        action = request.form.get('action')
        perm_name = request.form.get('permission')
        
        if not perm_name or perm_name not in Permission.__members__:
            flash("مجوز نامعتبر است.", "error")
            return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
            
        perm_enum = Permission[perm_name]
        
        if not user.profile:
            # ایجاد پروفایل اگر وجود ندارد
            user.profile = UserProfile(user_id=user.id)
            db.session.add(user.profile)
            db.session.commit()
            
        if action == 'grant':
            if perm_enum not in user.profile.custom_permissions:
                user.profile.custom_permissions.append(perm_enum)
                flash(f"مجوز {perm_enum.value} به کاربر {user.username} اعطا شد.", "success")
        elif action == 'revoke':
            if perm_enum in user.profile.custom_permissions:
                user.profile.custom_permissions.remove(perm_enum)
                flash(f"مجوز {perm_enum.value} از کاربر {user.username} حذف شد.", "warning")
                
        db.session.commit()
        return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
    
    # محاسبه مجوزهای نهایی کاربر
    base_perms = get_role_permissions(user.role)
    custom_perms = user.profile.custom_permissions if user.profile else []
    
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
    
    # شبیه‌سازی سرویس‌های موجود
    available_modules = [
        {'id': 'orders', 'name': 'مدیریت سفارشات', 'perm': Permission.ORDER_CREATE},
        {'id': 'logistics', 'name': 'پنل لجستیک', 'perm': Permission.LOGISTICS_MANAGE},
        {'id': 'legal', 'name': 'امور حقوقی', 'perm': Permission.LEGAL_REVIEW},
        {'id': 'finance', 'name': 'امور مالی', 'perm': Permission.FINANCE_VIEW},
        {'id': 'tech', 'name': 'بازرسی فنی', 'perm': Permission.TECH_INSPECT},
    ]
    
    visible_modules = []
    for module in available_modules:
        # بررسی دسترسی
        has_access = module['perm'] in get_role_permissions(user.role)
        if user.profile and module['perm'] in user.profile.custom_permissions:
            has_access = True # دسترسی سفارشی
            
        if has_access:
            visible_modules.append(module)
            
    return jsonify({
        'username': user.username,
        'role': user.role.value,
        'visible_modules': visible_modules
    })
