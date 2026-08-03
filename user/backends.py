from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpRequest
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)
Account = get_user_model()

class EnterpriseAuthBackend(ModelBackend):
    """Authenticates a user via email or username and enforces account lockout."""
    
    def authenticate(self, request: HttpRequest, username: Optional[str] = None, password: Optional[str] = None, **kwargs: Any) -> Optional[Any]:
        if username is None:
            username = kwargs.get(Account.USERNAME_FIELD)

        try:
            account = Account.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
        except Account.DoesNotExist:
            # Timing attack mitigation: Run hasher even if user doesn't exist
            Account().set_password(password)
            return None

        if account.is_locked():
            logger.warning(f"Attempted login on locked account: {username}")
            return None

        if account.check_password(password) and self.user_can_authenticate(account):
            account.reset_failed_logins()
            return account
        else:
            if account.role != Account.Role.ADMIN and not account.is_superuser:
                account.register_failed_login()
                if account.is_locked():
                    logger.warning(f"Account locked due to consecutive failed attempts: {username}")
            return None

    def get_user(self, user_id: Any) -> Optional[Any]:
        try:
            return Account.objects.get(pk=user_id)
        except Account.DoesNotExist:
            return None
        
        
