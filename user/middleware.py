from django.core.cache import cache
from django.http import JsonResponse, HttpRequest, HttpResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request: HttpRequest) -> str:
    # Cloudflare sets this at the edge with the real visitor IP and
    # overwrites any client-supplied value, so it cannot be spoofed --
    # PROVIDED inbound traffic to this server is firewalled to Cloudflare's
    # IP ranges only (DO Cloud Firewall + ufw), so requests can't bypass
    # Cloudflare and hit this server directly.
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip.strip()

    # Fallback only reached if CF-Connecting-IP is missing (e.g. Cloudflare
    # not in front of a request for some reason). Takes the last hop, not
    # the first, since a trusted proxy appends the real client IP as the
    # final entry -- the one part of the chain a client can't fake.
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()

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