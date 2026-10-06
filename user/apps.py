import os
import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)
def create_default_admin(sender, **kwargs) -> None:
    """Automatically creates the default super admin account from environment variables.
    Does nothing if the required env vars aren't set — no hardcoded fallback credentials."""
    from .models import Account

    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    admin_username = os.environ.get("DEFAULT_ADMIN_USERNAME")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

    if not admin_email or not admin_username or not admin_password:
        logger.warning(
            "DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD "
            "not all set — skipping default admin seeding."
        )
        return

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

def ready(self):
    import user.signals  # noqa: F401