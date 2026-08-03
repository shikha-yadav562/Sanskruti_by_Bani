import string
import secrets
import smtplib
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpRequest
from user_agents import parse
from .models import Account, PendingSignup, PasswordResetOTP, UsernameRecoveryOTP, LoginHistory, SecurityAuditLog
from .middleware import get_client_ip

logger = logging.getLogger(__name__)

def generate_secure_otp() -> str:
    """Generates a cryptographically secure 6-digit OTP using secrets module."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def send_html_email(subject: str, template_name: str, to_email: str, context: Dict[str, Any]) -> bool:
    """Handles robust email delivery with SMTP exception handling."""
    html_content = render_to_string(f'user/emails/{template_name}.html', context)
    text_content = f"Your code/info from Sanskruti By Bani is required. Please check your HTML email."
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@sanskruti.com'),
        to=[to_email]
    )
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Exception sending email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error sending email: {str(e)}")
        return False

def initiate_signup(data: Dict[str, str]) -> Dict[str, Any]:
    email = data['email']
    
    if Account.objects.filter(email=email).exists():
        # Enumeration protection inherently sacrificed at signup per spec feedback
        return {"success": False, "message": "Email is already registered."}
        
    pending, created = PendingSignup.objects.get_or_create(email=email)
    
    if not created:
        if not pending.can_resend():
            return {"success": False, "message": "Please wait 60 seconds before requesting a new OTP."}
        pending.resend_count += 1
    
    pending.username = data['username']
    pending.first_name = data.get('first_name', '')
    pending.last_name = data.get('last_name', '')
    pending.password_hash = data['password'] # Pre-hashed by the view
    
    raw_otp = generate_secure_otp()
    pending.set_otp(raw_otp)
    pending.save()
    
    email_sent = send_html_email(
        subject='Verify your account', 
        template_name='otp_email', 
        to_email=email, 
        context={'otp': raw_otp, 'expiration_minutes': PendingSignup.EXPIRY_MINUTES}
    )
    
    if not email_sent:
        pending.delete()
        return {"success": False, "message": "Unable to send email at this time. Please try again later."}
        
    return {"success": True, "message": "OTP sent successfully."}

def verify_signup(email: str, raw_otp: str) -> Dict[str, Any]:
    try:
        pending = PendingSignup.objects.get(email=email)
    except PendingSignup.DoesNotExist:
        return {"success": False, "message": "Session expired or invalid."}
        
    if pending.is_expired():
        return {"success": False, "message": "OTP has expired."}
        
    if not pending.check_otp(raw_otp):
        return {"success": False, "message": "Invalid OTP."}
        
    # Success - create account & completely destroy the OTP record
    account = Account.objects.create_user(
        email=pending.email,
        username=pending.username,
        password=None, # Already hashed, will set directly
        first_name=pending.first_name,
        last_name=pending.last_name,
        email_verified=True
    )
    account.password = pending.password_hash
    account.save()
    
    pending.delete()
    return {"success": True, "account": account}

def initiate_password_reset(account: Account) -> Dict[str, Any]:
    reset_otp, created = PasswordResetOTP.objects.get_or_create(account=account)
    
    if not created:
        if not reset_otp.can_resend():
            return {"success": False, "message": "Please wait before requesting a new OTP."}
        reset_otp.resend_count += 1
        
    raw_otp = generate_secure_otp()
    reset_otp.set_otp(raw_otp)
    reset_otp.save()
    
    email_sent = send_html_email(
        subject='Password Reset Request', 
        template_name='otp_email', 
        to_email=account.email, 
        context={'otp': raw_otp, 'expiration_minutes': PasswordResetOTP.EXPIRY_MINUTES}
    )
    
    if not email_sent:
        reset_otp.delete()
        return {"success": False, "message": "Unable to send email at this time."}
        
    return {"success": True, "message": "If the account exists, an OTP has been sent."}

def verify_and_reset_password(account: Account, raw_otp: str, new_password: str) -> Dict[str, Any]:
    try:
        reset_otp = PasswordResetOTP.objects.get(account=account)
    except PasswordResetOTP.DoesNotExist:
        return {"success": False, "message": "Invalid request."}
        
    if reset_otp.is_expired():
        return {"success": False, "message": "OTP has expired."}
        
    if not reset_otp.check_otp(raw_otp):
        return {"success": False, "message": "Invalid OTP."}
        
    account.set_password(new_password)
    account.reset_failed_logins() # Auto un-locks the account
    account.save()
    
    reset_otp.delete() # Explicit deletion of OTP
    
    SecurityAuditLog.objects.create(
        account=account,
        event="PASSWORD_RESET",
        detail="Password reset successfully via OTP"
    )
    
    return {"success": True, "message": "Password reset successfully. You can now login."}

def initiate_username_recovery(account: Account) -> Dict[str, Any]:
    recovery_otp, created = UsernameRecoveryOTP.objects.get_or_create(account=account)
    
    if not created:
        if not recovery_otp.can_resend():
            return {"success": False, "message": "Please wait before requesting a new OTP."}
        recovery_otp.resend_count += 1
        
    raw_otp = generate_secure_otp()
    recovery_otp.set_otp(raw_otp)
    recovery_otp.save()
    
    email_sent = send_html_email(
        subject='Username Recovery Code', 
        template_name='otp_email', 
        to_email=account.email, 
        context={'otp': raw_otp, 'expiration_minutes': UsernameRecoveryOTP.EXPIRY_MINUTES}
    )
    
    if not email_sent:
        recovery_otp.delete()
        return {"success": False, "message": "Unable to send email at this time."}
        
    return {"success": True, "message": "If the email matches our records, an OTP has been sent."}

def verify_and_send_username(account: Account, raw_otp: str) -> Dict[str, Any]:
    try:
        recovery_otp = UsernameRecoveryOTP.objects.get(account=account)
    except UsernameRecoveryOTP.DoesNotExist:
        return {"success": False, "message": "Invalid request."}
        
    if recovery_otp.is_expired():
        return {"success": False, "message": "OTP has expired."}
        
    if not recovery_otp.check_otp(raw_otp):
        return {"success": False, "message": "Invalid OTP."}
        
    email_sent = send_html_email(
        subject='Your Username Recovery', 
        template_name='username_email', 
        to_email=account.email, 
        context={'username': account.username, 'first_name': account.first_name}
    )
    
    if email_sent:
        recovery_otp.delete() # Explicit deletion of OTP
        return {"success": True, "message": "Your username has been sent to your email."}
    return {"success": False, "message": "Failed to send username email."}

def log_login_attempt(request: HttpRequest, account: Optional[Account], status: str, attempted_identifier: str = "", failure_reason: str = "") -> None:
    """Parses User-Agent and logs detailed authentication metrics."""
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    browser_str, os_str, device_str = 'Unknown', 'Unknown', 'Unknown'
    
    if ua_string:
        try:
            user_agent_parsed = parse(ua_string)
            browser_str = f"{user_agent_parsed.browser.family} {user_agent_parsed.browser.version_string}".strip()
            os_str = f"{user_agent_parsed.os.family} {user_agent_parsed.os.version_string}".strip()
            device_str = user_agent_parsed.device.family
        except Exception:
            pass

    LoginHistory.objects.create(
        account=account,
        attempted_identifier=attempted_identifier[:250],
        ip_address=get_client_ip(request),
        user_agent=ua_string[:500],
        browser=browser_str[:100],
        os=os_str[:100],
        device=device_str[:100],
        status=status,
        failure_reason=failure_reason
    )