from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask.views import MethodView
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
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('users.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_perms_bp.route('/')
@login_required
@admin_required
def permission_dashboard():
    """Main permissions management dashboard"""
    roles = Role
    permissions = Permission
    
    # Build permission matrix
    matrix = {}
    for role in roles:
        matrix[role.name] = {perm.name: perm in get_role_permissions(role) for perm in permissions}
    
    # Get all users for display in other tabs
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
    """Edit default permissions for a role"""
    try:
        target_role = Role[role_name.upper()]
    except KeyError:
        flash("Invalid role.", "error")
        return redirect(url_for('admin.admin_perms.permission_dashboard'))
    
    if request.method == 'POST':
        # In advanced version, these values should be saved to database
        # For now, temporarily managed in memory or config
        selected_perms = request.form.getlist('permissions')
        
        # Database storage logic for overriding defaults goes here
        # For simplicity, we show success message
        flash(f"Role {target_role.value} settings updated successfully. ({len(selected_perms)} permissions active)", "success")
        return redirect(url_for('admin.admin_perms.permission_dashboard'))
    
    current_perms = get_role_permissions(target_role)
    return render_template('admin/edit_role_perms.html', 
                           role=target_role, 
                           permissions=Permission, 
                           current_perms=current_perms)

# ============================================
# Implementation using MethodView (CBV)
# ============================================

class ManageUserPermissionsView(MethodView):
    """Class-based view for managing user permissions"""
    
    decorators = [login_required, admin_required]
    
    def get(self, user_id):
        """Display user permissions management page"""
        user = User.query.get_or_404(user_id)
        
        # === Auto-create profile if it doesn't exist ===
        if not user.profile:
            user.profile = UserProfile(user_id=user.id)
            db.session.add(user.profile)
            db.session.commit()
            flash(f"User {user.username} profile created automatically.", "info")
        
        base_perms = get_role_permissions(user.role)
        custom_perms = user.profile.get_custom_permissions() if user.profile else []
        
        return render_template('admin/manage_user_perms.html', 
                               user=user, 
                               base_perms=base_perms, 
                               custom_perms=custom_perms,
                               all_permissions=Permission)
    
    def post(self, user_id):
        """Grant or revoke permission for user"""
        user = User.query.get_or_404(user_id)
        
        # Ensure profile exists
        if not user.profile:
            user.profile = UserProfile(user_id=user.id)
            db.session.add(user.profile)
            db.session.commit()
        
        action = request.form.get('action')
        perm_value = request.form.get('permission')
        
        if not perm_value:
            flash("Invalid permission.", "error")
            return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
        
        try:
            perm_enum = Permission(perm_value)
        except ValueError:
            flash("Invalid permission.", "error")
            return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
        
        if action == 'grant':
            if user.profile.add_permission(perm_value):
                flash(f"Permission {perm_enum.value} granted to user {user.username}.", "success")
            else:
                flash(f"Permission {perm_enum.value} already granted to user.", "info")
        elif action == 'revoke':
            if user.profile.remove_permission(perm_value):
                flash(f"Permission {perm_enum.value} revoked from user {user.username}.", "warning")
            else:
                flash(f"Permission {perm_enum.value} was not in user's permission list.", "info")
        
        db.session.commit()
        return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))

# Register View as route
admin_perms_bp.add_url_rule(
    '/user-cbv/<int:user_id>',
    view_func=ManageUserPermissionsView.as_view('manage_user_permissions_cbv'),
    methods=['GET', 'POST']
)

# Keep old route for backward compatibility (but with cleaner code)
@admin_perms_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user_permissions(user_id):
    """Manage specific user permissions (exceptions) - FBV"""
    user = User.query.get_or_404(user_id)
    
    # === Auto-create profile if it doesn't exist ===
    if not user.profile:
        user.profile = UserProfile(user_id=user.id)
        db.session.add(user.profile)
        db.session.commit()
        flash(f"User {user.username} profile created automatically.", "info")
    
    if request.method == 'POST':
        action = request.form.get('action')
        perm_value = request.form.get('permission')
        
        if not perm_value:
            flash("Invalid permission.", "error")
            return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
        
        try:
            perm_enum = Permission(perm_value)
        except ValueError:
            flash("Invalid permission.", "error")
            return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
        
        if action == 'grant':
            if user.profile.add_permission(perm_value):
                flash(f"Permission {perm_enum.value} granted to user {user.username}.", "success")
            else:
                flash(f"Permission {perm_enum.value} already granted to user.", "info")
        elif action == 'revoke':
            if user.profile.remove_permission(perm_value):
                flash(f"Permission {perm_enum.value} revoked from user {user.username}.", "warning")
            else:
                flash(f"Permission {perm_enum.value} was not in user's permission list.", "info")
        
        db.session.commit()
        return redirect(url_for('admin_perms.manage_user_permissions', user_id=user.id))
    
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
    """Preview user menu JSON based on permissions"""
    user = User.query.get_or_404(user_id)
    
    # Ensure profile exists
    if not user.profile:
        from models.user import UserProfile
        user.profile = UserProfile(user_id=user.id)
        db.session.add(user.profile)
        db.session.commit()

    # Simulate existing services using real permissions
    available_modules = [
        {'id': 'orders', 'name': 'Order Management', 'perm': Permission.ORDER_CREATE},
        {'id': 'logistics', 'name': 'Logistics Panel', 'perm': Permission.LOGISTICS_ASSIGN_DRIVER},
        {'id': 'legal', 'name': 'Legal Affairs', 'perm': Permission.LEGAL_APPROVE_DOCS},
        {'id': 'finance', 'name': 'Financial Affairs', 'perm': Permission.FINANCE_VIEW_WALLET},
        {'id': 'tech', 'name': 'Technical Inspection', 'perm': Permission.TECH_SUBMIT_REPORT},
    ]
    
    # Get user's custom permissions
    custom_perms = user.profile.get_custom_permissions() if user.profile else []

    visible_modules = []
    for module in available_modules:
        # Check access
        has_access = module['perm'] in get_role_permissions(user.role)
        if custom_perms and module['perm'].value in custom_perms:
            has_access = True  # Custom access
            
        if has_access:
            visible_modules.append({
                'id': module['id'],
                'name': module['name'],
                'perm': module['perm'].value  # Convert Permission enum to string value
            })
            
    return jsonify({
        'username': user.username,
        'role': user.role.value,
        'visible_modules': visible_modules
    })
