from functools import wraps
from flask import flash, redirect, url_for, request, abort
from flask_login import current_user
from models.user import Role, UserProfile
from services.permissions import Permission, DEFAULT_ROLE_PERMISSIONS

def role_required(*roles):
    """
    دکوریتور برای محدود کردن دسترسی بر اساس نقش کاربر.
    
    Usage:
        @users_bp.route('/admin/panel')
        @login_required
        @role_required(Role.ADMIN)
        def admin_panel():
            ...
            
        @users_bp.route('/logistics/assign')
        @login_required
        @role_required(Role.LOGISTICS, Role.ADMIN)
        def assign_driver():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("لطفاً ابتدا وارد حساب کاربری خود شوید.", "error")
                return redirect(url_for('auth.login', next=request.url))
            
            if not hasattr(current_user, 'role') or current_user.role is None:
                flash("نقش کاربری تعریف نشده است.", "error")
                return redirect(url_for('users.profile'))
            
            if current_user.role not in roles:
                allowed_roles = [r.value for r in roles]
                flash(f"دسترسی غیرمجاز. این صفحه فقط برای نقش‌های {', '.join(allowed_roles)} قابل دسترسی است.", "error")
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(*permissions):
    """
    دکوریتور برای محدود کردن دسترسی بر اساس مجوزهای ریزدانه (Granular Permissions).
    این دکوریتور انعطاف‌پذیری بیشتری نسبت به role_required دارد و می‌توانید
    در پروفایل هر کاربر، مجوزها را شخصی‌سازی کنید.
    
    Usage:
        @users_bp.route('/order/create')
        @login_required
        @permission_required(Permission.ORDER_CREATE)
        def create_order():
            ...
            
        @users_bp.route('/logistics/update')
        @login_required
        @permission_required(Permission.LOGISTICS_UPDATE_STATUS)
        def update_logistics():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("لطفاً ابتدا وارد حساب کاربری خود شوید.", "error")
                return redirect(url_for('auth.login', next=request.url))
            
            user_permissions = get_user_permissions(current_user)
            
            # TODO: Translate -  Check اینکه آیا User حداقل یکی از Permissionهای موReject نیاز را داReject
            has_permission = any(perm in user_permissions for perm in permissions)
            
            if not has_permission:
                perm_names = [p.value for p in permissions]
                flash(f"دسترسی غیرمجاز. شما مجوز لازم ({', '.join(perm_names)}) را ندارید.", "error")
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_permissions(user):
    """
    دریافت لیست مجوزهای یک کاربر.
    اولویت‌بندی:
    1. اگر کاربر مجوزهای سفارشی در پروفایل خود دارد، آن مجوزها به عنوان مجوزهای نهایی استفاده می‌شوند.
    2. اگر مجوز سفارشی وجود ندارد، از مجوزهای پیش‌فرض نقش (DEFAULT_ROLE_PERMISSIONS) استفاده می‌شود.
    3. اگر کاربر مهمان است، مجوزهای guest بازگردانده می‌شود.
    
    Returns:
        لیستی از اشیاء Permission
    """
    import json
    
    if not user.is_authenticated:
        return DEFAULT_ROLE_PERMISSIONS.get('guest', [])
    
    # Try to get custom permissions from user profile first
    # Use the relationship if available, otherwise query
    profile = None
    if hasattr(user, 'profile') and user.profile:
        profile = user.profile
    else:
        try:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
        except Exception:
            # If database is not available, skip custom permissions
            pass
    
    if profile and profile.custom_permissions:
        # TODO: Translate -  اگر User Permissionهای دستی تنظیم کRejectه باشد
        from services.permissions import Permission as PermEnum
        custom_perms = []
        
        # Parse JSON string to list
        try:
            if isinstance(profile.custom_permissions, str):
                perm_strings = json.loads(profile.custom_permissions)
            else:
                perm_strings = profile.custom_permissions
            
            if perm_strings:  # TODO: Translate -  اگر List خالی نباشد
                for perm_str in perm_strings:
                    try:
                        # TODO: Translate -  پشتیبانی از هر دو فرمت: String و شیء Permission
                        if isinstance(perm_str, PermEnum):
                            custom_perms.append(perm_str)
                        else:
                            perm = PermEnum(str(perm_str))
                            custom_perms.append(perm)
                    except ValueError:
                        continue  # TODO: Translate -  نادیده گرفتن Permissionهای نامعتبر
                
                # TODO: Translate -  اگر Permission Orderی معتبر وجود داشت، برگRejectان
                if custom_perms:
                    return custom_perms
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass  # TODO: Translate -  اگر JSON نامعتبر بود، از Default استفاده کن
    
    # TODO: Translate -  استفاده از Permissionهای Default Role
    role_name = user.role.value if user.role else 'guest'
    return DEFAULT_ROLE_PERMISSIONS.get(role_name, [])


def has_permission(user, permission):
    """
    بررسی ساده اینکه آیا یک کاربر مجوز خاصی دارد یا خیر.
    مناسب برای استفاده در templateها.
    
    Usage in template:
        {% if has_permission(current_user, Permission.ORDER_CREATE) %}
            <a href="/order/create">ثبت سفارش جدید</a>
        {% endif %}
    """
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def get_role_permissions(role):
    """
    دریافت مجوزهای پیش‌فرض یک نقش خاص.
    
    Args:
        role: شیء Role یا رشته نام نقش
        
    Returns:
        لیستی از مجوزهای Permission مربوط به آن نقش
    """
    from models.user import Role
    
    # TODO: Translate -  تبدیل به String اگر Role object باشد
    if isinstance(role, Role):
        role_name = role.value
    else:
        role_name = str(role)
    
    return DEFAULT_ROLE_PERMISSIONS.get(role_name, [])


def service_module_enabled(service_name, user=None):
    """
    بررسی اینکه آیا یک ماژول خدماتی برای کاربر فعال است یا خیر.
    این تابع برای نمایش/مخفی کردن بخش‌های مختلف در UI بر اساس نقش و تنظیمات پروفایل استفاده می‌شود.
    
    Args:
        service_name: نام سرویس (مثلاً 'logistics', 'legal', 'investment')
        user: شیء کاربر (اگر None باشد، از current_user استفاده می‌کند)
    
    Returns:
        Boolean: True اگر سرویس برای کاربر فعال باشد
    """
    from flask_login import current_user as cu
    if user is None:
        user = cu
    
    if not user.is_authenticated:
        return False
    
    # TODO: Translate -  نگاشت نام Service به Permission مربوطه
    service_permission_map = {
        'order': Permission.ORDER_VIEW,
        'logistics': Permission.LOGISTICS_VIEW_ASSIGNED,
        'legal': Permission.LEGAL_VIEW_CONTRACTS,
        'finance': Permission.FINANCE_VIEW_WALLET,
        'investment': Permission.INVESTMENT_VIEW_PORTFOLIO,
        'technical': Permission.TECH_VIEW_INSPECTIONS,
        'dashboard': Permission.DASHBOARD_VIEW_STATS,
    }
    
    required_permission = service_permission_map.get(service_name)
    if not required_permission:
        return False
    
    return has_permission(user, required_permission)
