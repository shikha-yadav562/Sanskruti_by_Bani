import os

# ==============================================================================
# Add these securely to your main Django settings.py file for Enterprise Production
# ==============================================================================

# Custom User Model definition
AUTH_USER_MODEL = 'user.Account'

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    'user.backends.EnterpriseAuthBackend',
]

# Ensure you have 'user.middleware.IPRateLimitMiddleware' in your MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middleware.IPRateLimitMiddleware', # IP-Based Brute Force Protection
]

# Caching for Rate Limiting (Using local memory for standalone, switch to Redis for clustered)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'enterprise-rate-limit',
    }
}

# Security Headers (Uncomment for Production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookies (Requires HTTPS)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'