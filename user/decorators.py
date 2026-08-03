from functools import wraps
from django.http import HttpResponseForbidden, HttpResponse, HttpRequest
from django.shortcuts import redirect
from typing import Callable, Any

def admin_required(view_func: Callable) -> Callable:
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('user:login')
        if request.user.role != 'admin':
            return HttpResponseForbidden("Access Denied: Administrators only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_required(view_func: Callable) -> Callable:
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('user:login')
        if request.user.role != 'user':
            return HttpResponseForbidden("Access Denied: Standard users only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view