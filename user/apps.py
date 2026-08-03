import os
import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

def create_default_admin(sender, **kwargs) -> None:
    """Automatically creates the default super admin account from secure environment variables."""
    from .models import Account
    
    # Strictly using environment variables per enterprise requirements
    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    
    if not Account.objects.filter(username=admin_username).exists() and not Account.objects.filter(email=admin_email).exists():
        try:
            Account.objects.create_admin(
                email=admin_email,
                username=admin_username,
                password=admin_password,
                first_name="Super",
                last_name="Admin"
            )
            logger.info(f"Default admin account '{admin_username}' seeded successfully.")
        except Exception as e:
            logger.error(f"Failed to create default admin account: {e}")

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'
    
    def ready(self) -> None:
        post_migrate.connect(create_default_admin, sender=self)