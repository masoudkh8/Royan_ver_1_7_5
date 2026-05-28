
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from models import db
from models.user import User, UserProfile, Role
from services.permissions import Permission, DEFAULT_ROLE_PERMISSIONS
from services.access_control import role_required, permission_required, get_user_permissions, has_permission
import json

# users_bp = Blueprint('users', __name__, url_prefix='/users')
# استفاده از users_bp مشترک از __init__.py
from . import users_bp


# ============================================
# پیاده‌سازی با استفاده از MethodView (CBV)
# ============================================

class ManagePermissionsView(MethodView):
    """نمای مبتنی بر کلاس برای مدیریت مجوزها"""
    
    decorators = [login_required, role_required(Role.ADMIN)]
    
    def get(self):
        """نمایش صفحه مدیریت مجوزها"""
        from models.user import UserProfile
        import json
        
        target_user_id = request.args.get('target_user_id')
        
        if target_user_id:
            try:
                target_user_id = int(target_user_id)
            except (ValueError, TypeError):
                target_user_id = current_user.id
        else:
            target_user_id = current_user.id
        
        target_user = User.query.get_or_404(target_user_id)
        
        # ایجاد خودکار پروفایل اگر وجود ندارد
        if not target_user.profile:
            target_profile = UserProfile(user_id=target_user.id)
            db.session.add(target_profile)
            db.session.commit()
            flash(f"پروفایل کاربر {target_user.username} به صورت خودکار ایجاد شد.", "info")
        else:
            target_profile = target_user.profile
        
        default_perms = DEFAULT_ROLE_PERMISSIONS.get(target_user.role.value if target_user.role else 'guest', [])
        custom_perms = target_profile.get_custom_permissions() if target_profile else []
        
        all_permissions = [
            {
                'value': perm.value,
                'name': perm.name,
                'category': _get_permission_category(perm),
                'is_enabled': perm.value in custom_perms if custom_perms else perm in default_perms
            }
            for perm in Permission
        ]
        
        categories = {}
        for perm in all_permissions:
            cat = perm['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(perm)
        
        users_list = User.query.order_by(User.username).all() if current_user.role == Role.ADMIN else []
        
        return render_template('users/manage_permissions.html',
                             categories=categories,
                             default_perms=[p.value for p in default_perms],
                             custom_perms=custom_perms,
                             users_list=users_list,
                             current_user_obj=current_user,
                             target_user=target_user)
    
    def post(self):
        """ذخیره تغییرات مجوزها"""
        from flask_wtf.csrf import validate_csrf
        from wtforms.validators import ValidationError
        from models.user import UserProfile
        
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash("خطای امنیتی: توکن CSRF نامعتبر است.", "error")
            return redirect(url_for('users.manage_permissions'))
        
        target_user_id = request.form.get('target_user_id') or current_user.id
        
        try:
            target_user_id = int(target_user_id)
        except (ValueError, TypeError):
            target_user_id = current_user.id
        
        target_user = User.query.get_or_404(target_user_id)
        
        if not target_user.profile:
            target_profile = UserProfile(user_id=target_user.id)
            db.session.add(target_profile)
            db.session.commit()
        else:
            target_profile = target_user.profile
        
        selected_permissions = request.form.getlist('permissions')
        
        valid_permissions = []
        for perm_value in selected_permissions:
            try:
                Permission(perm_value)
                valid_permissions.append(perm_value)
            except ValueError:
                continue
        
        if valid_permissions:
            target_profile.set_custom_permissions(valid_permissions)
            flash(f"مجوزهای کاربر {target_user.username} با موفقیت به‌روزرسانی شد. ({len(valid_permissions)} مجوز فعال)", "success")
        else:
            target_profile.set_custom_permissions([])
            flash(f"مجوزهای کاربر {target_user.username} به حالت پیش‌فرض بازگشت.", "info")
        
        db.session.commit()
        return redirect(url_for('users.manage_permissions', target_user_id=target_user.id))

# ثبت View به عنوان route
users_bp.add_url_rule(
    '/profile/permissions-cbv',
    view_func=ManagePermissionsView.as_view('manage_permissions_cbv'),
    methods=['GET', 'POST']
)


@users_bp.route('/profile/permissions', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def manage_permissions():
    """
    مدیریت مجوزهای سفارشی برای کاربر - FBV (Function Based View)
    فقط ادمین می‌تواند برای هر کاربر مجوزهای خاصی را فعال/غیرفعال کند.
    """
    from models.user import UserProfile
    import json
    
    # دریافت target_user_id از query parameter یا form
    target_user_id = request.args.get('target_user_id') or request.form.get('target_user_id')
    
    # اگر target_user_id مشخص نشده، از کاربر فعلی استفاده کن (فقط برای مشاهده)
    if target_user_id:
        try:
            target_user_id = int(target_user_id)
        except (ValueError, TypeError):
            target_user_id = current_user.id
    else:
        target_user_id = current_user.id
    
    target_user = User.query.get_or_404(target_user_id)
    
    # === ایجاد خودکار پروفایل اگر وجود ندارد ===
    if not target_user.profile:
        target_profile = UserProfile(user_id=target_user.id)
        db.session.add(target_profile)
        db.session.commit()
        flash(f"پروفایل کاربر {target_user.username} به صورت خودکار ایجاد شد.", "info")
    else:
        target_profile = target_user.profile
    
    # دریافت مجوزهای پیش‌فرض نقش کاربر هدف
    default_perms = DEFAULT_ROLE_PERMISSIONS.get(target_user.role.value if target_user.role else 'guest', [])
    
    # دریافت مجوزهای سفارشی با استفاده از متد جدید مدل
    custom_perms = target_profile.get_custom_permissions() if target_profile else []
    
    # تبدیل به فرمت مناسب برای نمایش
    all_permissions = [
        {
            'value': perm.value,
            'name': perm.name,
            'category': _get_permission_category(perm),
            'is_enabled': perm.value in custom_perms if custom_perms else perm in default_perms
        }
        for perm in Permission
    ]
    
    # گروه‌بندی بر اساس دسته‌بندی
    categories = {}
    for perm in all_permissions:
        cat = perm['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(perm)
    
    if request.method == 'POST':
        # بررسی CSRF Token
        from flask_wtf.csrf import validate_csrf
        from wtforms.validators import ValidationError
        
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash("خطای امنیتی: توکن CSRF نامعتبر است.", "error")
            return redirect(url_for('users.manage_permissions'))
        
        # دریافت لیست مجوزهای انتخاب شده از فرم
        selected_permissions = request.form.getlist('permissions')
        
        # اعتبارسنجی و فیلتر کردن مجوزهای معتبر
        valid_permissions = []
        for perm_value in selected_permissions:
            try:
                # اطمینان از معتبر بودن مجوز
                Permission(perm_value)
                valid_permissions.append(perm_value)
            except ValueError:
                continue  # نادیده گرفتن مجوزهای نامعتبر
        
        # استفاده از متدهای جدید مدل برای ذخیره مجوزها
        if valid_permissions:
            target_profile.set_custom_permissions(valid_permissions)
            flash(f"مجوزهای کاربر {target_user.username} با موفقیت به‌روزرسانی شد. ({len(valid_permissions)} مجوز فعال)", "success")
        else:
            target_profile.set_custom_permissions([])
            flash(f"مجوزهای کاربر {target_user.username} به حالت پیش‌فرض بازگشت.", "info")
        
        db.session.commit()
        return redirect(url_for('users.manage_permissions', target_user_id=target_user.id))
    
    # اگر کاربر ادمین است، لیست کاربران را برای انتخاب بفرست
    users_list = []
    if current_user.role == Role.ADMIN:
        users_list = User.query.order_by(User.username).all()
    
    return render_template('users/manage_permissions.html',
                         categories=categories,
                         default_perms=[p.value for p in default_perms],  # تبدیل به لیست رشته‌ها
                         custom_perms=custom_perms,
                         users_list=users_list,
                         current_user_obj=current_user,
                         target_user=target_user)


def _get_permission_category(permission):
    """تعیین دسته‌بندی هر مجوز"""
    category_map = {
        'ORDER': 'سفارشات',
        'LOGISTICS': 'لجستیک',
        'LEGAL': 'حقوقی',
        'FINANCE': 'مالی',
        'INVESTMENT': 'سرمایه‌گذاری',
        'TECH': 'فنی',
        'DASHBOARD': 'داشبورد',
        'PROFILE': 'پروفایل',
        'PUBLIC': 'عمومی',
    }
    
    for prefix, category in category_map.items():
        if permission.name.startswith(prefix):
            return category
    
    return 'سایر'


@users_bp.route('/dashboard')
@login_required
def dashboard():
    """
    داشبورد هوشمند که بر اساس نقش و مجوزهای کاربر، سرویس‌های مرتبط را نمایش می‌دهد.
    """
    from services.access_control import service_module_enabled
    from models.notification import Notification
    
    # بررسی دسترسی به ماژول‌های مختلف
    modules = {
        'order': service_module_enabled('order'),
        'logistics': service_module_enabled('logistics'),
        'legal': service_module_enabled('legal'),
        'finance': service_module_enabled('finance'),
        'investment': service_module_enabled('investment'),
        'technical': service_module_enabled('technical'),
        'dashboard': service_module_enabled('dashboard'),
    }
    
    # دریافت آمارهای مرتبط بر اساس نقش
    stats = _get_user_stats(current_user)
    
    # محاسبه تعداد اعلان‌های خوانده‌نشده
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # تعیین وضعیت تأیید مدارک
    import json
    verification_docs = json.loads(current_user.verification_documents) if current_user.verification_documents else []
    document_status = 'not_uploaded'
    if verification_docs:
        document_status = 'pending'
        if current_user.is_verified:
            document_status = 'approved'
    
    # ادغام داشبورد ماژولار در dashboard.html اصلی برای یکپارچگی
    return render_template('users/dashboard.html', 
                         modules=modules, 
                         stats=stats,
                         user=current_user,
                         user_role=current_user.role.value,
                         unread_notifications=unread_notifications,
                         document_status=document_status,
                         pending_orders=stats.get('pending_orders', 0))


def _get_user_stats(user):
    """دریافت آمارهای مرتبط با کاربر بر اساس نقش"""
    stats = {}
    
    # مثال: آمار سفارشات
    if user.role in [Role.BUYER, Role.PRODUCER, Role.BROKER]:
        from models.order import Order
        user_orders = Order.query.filter(
            db.or_(
                Order.buyer_id == user.id,
                Order.seller_id == user.id,
                Order.broker_id == user.id
            )
        ).all()
        stats['total_orders'] = len(user_orders)
        stats['pending_orders'] = len([o for o in user_orders if o.status.value == 'pending'])
    
    # مثال: آمار لجستیک
    if user.role == Role.LOGISTICS:
        from models.order import Order
        logistics_orders = Order.query.filter_by(logistics_provider_id=user.id).all()
        stats['assigned_shipments'] = len(logistics_orders)
        stats['in_transit'] = len([o for o in logistics_orders if o.status.value == 'in_transit'])
    
    # مثال: آمار سرمایه‌گذاری
    if user.role == Role.INVESTOR:
        stats['portfolio_value'] = 0  # TODO: محاسبه از مدل Investment
        stats['active_investments'] = 0
    
    return stats


@users_bp.route('/logistics/orders')
@login_required
@role_required(Role.LOGISTICS, Role.ADMIN)
def logistics_orders():
    """نمایش سفارش‌های اختصاص یافته به ارائه‌دهنده لجستیک"""
    from models.order import Order
    
    orders = Order.query.filter_by(logistics_provider_id=current_user.id).all()
    return render_template('users/logistics_orders.html', orders=orders)


@users_bp.route('/legal/reviews')
@login_required
@role_required(Role.LEGAL, Role.ADMIN)
def legal_reviews():
    """نمایش قراردادهای نیازمند بررسی حقوقی"""
    from models.order import Order
    
    orders = Order.query.filter_by(legal_advisor_id=current_user.id).all()
    return render_template('users/legal_reviews.html', orders=orders)


@users_bp.route('/technical/inspections')
@login_required
@role_required(Role.TECH_PARTNER, Role.ADMIN)
def technical_inspections():
    """نمایش درخواست‌های بازرسی فنی"""
    from models.order import Order
    
    orders = Order.query.filter_by(tech_partner_id=current_user.id).all()
    return render_template('users/technical_inspections.html', orders=orders)


@users_bp.route('/investment/portfolio')
@login_required
@role_required(Role.INVESTOR, Role.ADMIN)
def investment_portfolio():
    """نمایش پورتفوی سرمایه‌گذاری"""
    # TODO: پیاده‌سازی مدل Investment و ارتباط آن با کاربر
    investments = []  # Investment.query.filter_by(investor_id=current_user.id).all()
    return render_template('users/investment_portfolio.html', investments=investments)


@users_bp.route('/corporate/approvals')
@login_required
@role_required(Role.CORPORATE_AGENT, Role.ADMIN)
def corporate_approvals():
    """نمایش تأییدیه‌های شرکتی مورد نیاز"""
    from models.order import Order
    
    orders = Order.query.filter_by(corporate_agent_id=current_user.id).all()
    return render_template('users/corporate_approvals.html', orders=orders)


@users_bp.route('/broker/commissions')
@login_required
@role_required(Role.BROKER, Role.ADMIN)
def broker_commissions():
    """نمایش کمیسیون‌های کارگزاری"""
    from models.order import Order
    
    orders = Order.query.filter_by(broker_id=current_user.id).all()
    total_commission = sum(o.commission_amount or 0 for o in orders)
    
    return render_template('users/broker_commissions.html', 
                         orders=orders, 
                         total_commission=total_commission)
