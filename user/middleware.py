from django.core.cache import cache
from django.http import JsonResponse, HttpRequest, HttpResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')

class IPRateLimitMiddleware:
    """IP-Based Rate Limiting for Authentication Endpoints"""
    
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only throttle authentication API routes
        if request.path.startswith('/api/auth/'):
            ip = get_client_ip(request)
            
            # Stricter limits for login vs other auth routes
            if 'login' in request.path:
                max_attempts = 15
                timeout_seconds = 3600 # 1 hour
                prefix = 'ratelimit_login_'
            else:
                max_attempts = 30
                timeout_seconds = 3600
                prefix = 'ratelimit_auth_'
                
            key = f"{prefix}{ip}"
            attempts = cache.get(key, 0)
            
            if attempts >= max_attempts:
                logger.warning(f"IP Rate limit triggered for IP: {ip} on path {request.path}")
                return JsonResponse({
                    'error': 'Too many requests from this IP address. Please try again later.'
                }, status=429)
                
            cache.set(key, attempts + 1, timeout_seconds)
            
        return self.get_response(request)