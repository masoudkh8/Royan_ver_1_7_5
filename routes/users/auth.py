import random
import logging
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Message
from models import db
from models.premium_request import PremiumRequest
from . import users_bp
from datetime import datetime
import pytz
from extensions import mail
from kavenegar import KavenegarAPI

tehran_tz = pytz.timezone('Asia/Tehran')
logger = logging.getLogger(__name__)


def get_serializer():
    """Create a URL-safe timed serializer for email tokens."""
    return URLSafeTimedSerializer(current_app.secret_key)


def send_sms(phone, message):
    """Send SMS via Kavenegar API with proper error handling and logging."""
    if not phone:
        logger.error("The mobile number is empty.")
        return False

    # Clean phone number (remove leading zero)
    cleaned_phone = phone
    if cleaned_phone.startswith("0"):
        cleaned_phone = cleaned_phone[1:]
    
    if not cleaned_phone.isdigit() or len(cleaned_phone) != 10:
        logger.error(f"Invalid number format: {phone}")
        return False

    # Debug mode: just log without sending
    if current_app.config.get('D_STATE'):
        logger.info(f"[TEST] SMS to {phone}: {message}")
        return True

    # Production mode: send actual SMS
    try:
        api_key = current_app.config.get('KAVENEGAR_API_KEY')

        if not api_key:
            logger.error("Kavenegar API key not configured")
            return False
            
        api = KavenegarAPI(api_key)
        params = {'sender': '2000660110', 'receptor': phone, 'message': message}
        response = api.sms_send(params)

        if response.status_code == 200:
            json_resp = response.json()
            if json_resp["return"]["status"] == 200:
                logger.info(f"SMS to {phone} sent successfully.")
                return True
            else:
                logger.error(f"Kavenegar error: {json_resp['return']['message']}")
                return False
        else:
            logger.error(f"HTTP error: {response.status_code}, response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False



@users_bp.route('/verify_phone', methods=['GET', 'POST'])
@login_required
def verify_phone():
    if not current_user.phone or not current_user.phone.strip():
        flash("❌ Please enter your mobile number in your profile first.")
        return redirect(url_for('users.profile'))

    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()

    # اگر درخواستی وجود ندارد، یک درخواست جدید با وضعیت draft ایجاد کن
    if not req:
        req = PremiumRequest(
            user_id=current_user.id,
            requested_phone=current_user.phone,
            status='draft',  # ✅ تغییر از 'pending' به 'draft'
        )
        db.session.add(req)
        db.session.commit()

    # اگر شماره قبلاً تأیید شده، به مرحله بعد برو
    if req.phone_verified:
        flash("✅ Your mobile number has already been verified.")
        return redirect(url_for('users.verify_email'))  # ✅ به ایمیل برو، نه payment_confirmation

    if request.method == 'POST':
        if 'resend' in request.form:
            code = str(random.randint(100000, 999999))
            req.phone_verification_code = code
            db.session.commit()
            try:
                send_sms(current_user.phone, f"Verification code: {code}")
                flash("New code sent.")
            except Exception as e:
                current_app.logger.error(f"SMS failed: {e}")
                flash("❌ There was a problem sending the code.")
            return redirect(url_for('users.verify_phone'))

        code = request.form.get('code', '').strip()
        if not code:
            flash("Please enter the code.")
        elif code == req.phone_verification_code:
            req.phone_verified = True
            req.phone_verification_code = None
            db.session.commit()
            flash("✅ Mobile number successfully verified.")
            return redirect(url_for('users.verify_email'))  # ✅ بعد از تأیید شماره، به ایمیل برو
        else:
            flash("❌ The code is invalid.")

    # ارسال اولیه کد
    if not req.phone_verification_code:
        code = str(random.randint(100000, 999999))
        req.phone_verification_code = code
        db.session.commit()
        try:
            send_sms(current_user.phone, f"Verification code: {code}")
            flash("A verification code has been sent to your number.")
        except Exception as e:
            current_app.logger.error(f"SMS failed: {e}")
            flash("❌ There was a problem sending the code.")

    return render_template('users/verify_phone.html', req=req)







# -------------------------------
# تأیید ایمیل (صفحه نمایش)
# -------------------------------
@users_bp.route('/verify_email')
@login_required
def verify_email():
    print('start email process')
    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()
    # if not req:
    #     print('if not req')
    #     return redirect(url_for('users.upgrade_to_premium'))

    if not req or not req.phone_verified:
        return redirect(url_for('users.verify_phone'))


    if req.email_verified:
        print('req.email_verified')
        return redirect(url_for('users.upload_documents'))

    # if req.email_verification_token:
    #     print(req.email_verification_token)

    if not req.email_verification_token:
        # print('not req.email_verification_token')
        if send_email_verification(current_user):
            # print('....... send_email_verification')
            flash("Confirmation email sent.")
        else:
            print('....... ❌❌')
            flash("❌ There was an error sending the email.")
            return render_template('users/verify_email.html', req=req)

    return render_template('users/verify_email.html', req=req)


# ارسال ایمیل تأیید
def send_email_verification(user):

    print('send email func')
    serializer = get_serializer()
    token = serializer.dumps(user.email, salt='email-verify-salt')

    req = PremiumRequest.query.filter_by(user_id=user.id).order_by(PremiumRequest.submitted_at.desc()).first()
    print(req)
    if req:
        req.email_verification_token = token
        db.session.commit()

    confirm_url = url_for('users.confirm_email', token=token, _external=True)

    html_body = f"""
    <h2>Hello {user.username}!</h2>
    <p>Verify your email to complete the upgrade process to a premium user:</p>
    <p><a href="{confirm_url}">✅ Email verification</a></p>
    <p>This link will expire after 24 hours.</p>
    """

    msg = Message(
        subject="✅ Email Verification - Upgrade Process",
        recipients=[user.email],
        html=html_body,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER')
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


# -------------------------------
# تأیید توکن ایمیل
# -------------------------------
@users_bp.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    print('start confirm_email func')
    s = get_serializer()
    try:
        email = s.loads(token, salt='email-verify-salt', max_age=86400)
    except SignatureExpired:
        flash("❌ The link has expired.")
        return redirect(url_for('users.verify_email'))
    except BadSignature:
        flash("❌ The link is invalid.")
        return redirect(url_for('users.upgrade_to_premium'))

    if email != current_user.email:
        flash("❌ This link is not for you.")
        return redirect(url_for('users.login'))

    req = PremiumRequest.query.filter_by(user_id=current_user.id).order_by(PremiumRequest.submitted_at.desc()).first()
    if not req:
        flash("❌ No request found.")
        return redirect(url_for('users.upgrade_to_premium'))

    if not req.email_verified:
        req.email_verified = True
        req.email_verification_token = None
        db.session.commit()
        flash("✅ Email has been verified.")

    return redirect(url_for('users.upload_documents'))