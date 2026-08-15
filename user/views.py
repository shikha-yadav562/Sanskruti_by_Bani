from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignupForm, LoginForm
from adm_user.models import AboutUsSection, HeroSlideOffer, HeroSlideMain, HeroSlideImageOnly, HeaderSettings, OfferBarItem, FooterSettings, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3, SignatureCategoryItem

# Create your views here.
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Address, ProductReview, ReviewHelpful

# Create your views here.
def index(request):
    context = {
        "hero_main": HeroSlideMain.load(),
        "hero_image_only": HeroSlideImageOnly.load(),
        "header_settings": HeaderSettings.load(),
        "offer_items": OfferBarItem.objects.all(), 
        "footer_settings": FooterSettings.load(), 
        "about_section": AboutUsSection.load(),
        "memories_section": SweetMemoriesSection.load(),
        "memory_images": SweetMemoryImage.objects.all(),
        "memories_offer_slide": MemoriesOfferSlide.load(),
        "memories_slide3": MemoriesSlide3.load(),
        "signature_categories": SignatureCategoryItem.objects.filter(is_active=True),
    }
    return render(request, 'user/index.html', context)

def product(request):
    reviews = ProductReview.objects.filter(is_approved=True)
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    avg_rating_formatted = round(avg_rating, 1)

    # Star rating breakdown
    star_counts = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }

    star_percents = {}
    for star, count in star_counts.items():
        star_percents[star] = round((count / total_reviews * 100)) if total_reviews > 0 else 0

    # Customer photos from reviews
    customer_photos = []
    for r in reviews:
        if r.image_1: customer_photos.append(r.image_1)
        if r.image_2: customer_photos.append(r.image_2)
        if r.image_3: customer_photos.append(r.image_3)

    context = {
        "header_settings": HeaderSettings.load(),
        "footer_settings": FooterSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating_formatted,
        "star_counts": star_counts,
        "star_percents": star_percents,
        "customer_photos": customer_photos,
    }
    return render(request, 'user/product.html', context)

def catalogue(request):
    return render(request, 'user/catalogue.html')

def profile_view(request):
    context = {
        "header_settings": HeaderSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "footer_settings": FooterSettings.load(),
    }
    return render(request, 'user/profile.html', context)

def terms_conditions(request):
    context = {
        "header_settings": HeaderSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "footer_settings": FooterSettings.load(),
    }
    return render(request, 'user/terms_conditions.html', context)

def return_refund_policy(request):
    context = {
        "header_settings": HeaderSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "footer_settings": FooterSettings.load(),
    }
    return render(request, 'user/return_refund_policy.html', context)

def privacy_policy(request):
    context = {
        "header_settings": HeaderSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "footer_settings": FooterSettings.load(),
    }
    return render(request, 'user/privacy_policy.html', context)


# def signup_view(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.email = form.cleaned_data['email']
#             user.save()
#             auth_login(request, user)
#             return redirect('user:index')
#     else:
#         form = SignupForm()
#     return render(request, 'user/signup.html', {'form': form})


# def login_view(request):
#     if request.method == 'POST':
#         email = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(request, username=email, password=password)

#         if user is not None:
#             auth_login(request, user)
#             if user.is_staff or user.is_superuser:
#                 return redirect('adm_user:dashboard')
#             return redirect('user:index')
#         else:
#             messages.error(request, 'Invalid email or password.')

#     return render(request, 'user/login.html')


# @login_required
# def logout_view(request):
#     auth_logout(request)
#     return redirect('user:login')

#====================================================================================
#-------------------------LOGIN AND SIGNUP------------------------------------------
#====================================================================================

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from . import services
from .models import LoginHistory

Account = get_user_model()

def login_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('adm_user:dashboard' if request.user.role == 'admin' else 'user:dashboard')
    return render(request, 'user/login.html')

def signup_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('adm_user:dashboard' if request.user.role == 'admin' else 'user:dashboard')
    return render(request, 'user/signup.html')

def api_login(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        account = authenticate(request, username=username, password=password)
        
        if account:
            login(request, account)
            request.session.cycle_key() # Session rotation
            
            if not remember_me:
                request.session.set_expiry(0) 
            else:
                request.session.set_expiry(30 * 24 * 60 * 60)
                
            services.log_login_attempt(request, account, "success", attempted_identifier=username)
            redirect_url = '/adm/' if account.role == 'admin' else '/'
            return JsonResponse({"success": True, "redirect_url": redirect_url})
            
        else:
            try:
                failed_account = Account.objects.get(email=username) if '@' in username else Account.objects.get(username=username)
                if failed_account.is_locked():
                    lock_mins = int((failed_account.locked_until - timezone.now()).total_seconds() / 60)
                    services.log_login_attempt(request, failed_account, "failed", attempted_identifier=username, failure_reason="Account locked")
                    return JsonResponse({"error": f"Account locked. Try again in {lock_mins} minutes."}, status=403)
                services.log_login_attempt(request, failed_account, "failed", attempted_identifier=username, failure_reason="Invalid password")
            except Account.DoesNotExist:
                services.log_login_attempt(request, None, "failed", attempted_identifier=username, failure_reason="User not found")
                
            return JsonResponse({"error": "Invalid credentials provided."}, status=401)
            
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)

def api_logout(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        if request.user.is_authenticated:
            history = LoginHistory.objects.filter(account=request.user, logout_time__isnull=True).order_by('-login_time').first()
            if history:
                history.logout_time = timezone.now()
                history.save(update_fields=['logout_time'])
                
            logout(request)
            request.session.flush() # Destroy Django Session
        return JsonResponse({"success": True, "redirect_url": "/login/"})
    return JsonResponse({"error": "Method not allowed"}, status=405)

@transaction.atomic
def api_signup_init(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    data = json.loads(request.body)
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password')
    full_name = data.get('full_name', '').strip()
    
    parts = full_name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    if Account.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username is already taken."}, status=400)
        
    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({"error": e.messages[0]}, status=400)
        
    # Pre-hash password before passing to service
    data['password'] = make_password(password)
    data['first_name'] = first_name
    data['last_name'] = last_name
    
    result = services.initiate_signup(data)
    if result['success']:
        request.session['signup_email'] = email # Keep track of who is signing up
        return JsonResponse({"success": True, "message": result['message']})
    return JsonResponse({"error": result['message']}, status=429)

@transaction.atomic
def api_signup_verify(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    data = json.loads(request.body)
    otp = data.get('otp')
    email = request.session.get('signup_email')
    
    if not email:
        return JsonResponse({"error": "Session expired. Please sign up again."}, status=400)
        
    result = services.verify_signup(email, otp)
    
    if not result['success']:
        return JsonResponse({"error": result['message']}, status=400)
        
    account = result['account']
    del request.session['signup_email']
    
    login(request, account)
    request.session.cycle_key()
    services.log_login_attempt(request, account, "success", attempted_identifier=account.email)
    
    return JsonResponse({"success": True, "redirect_url": "/"})

def api_forgot_password_init(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    data = json.loads(request.body)
    identifier = data.get('email', '').strip().lower()
    
    try:
        account = Account.objects.get(Q(email=identifier) | Q(username=identifier))
        result = services.initiate_password_reset(account)
        if not result['success']:
            return JsonResponse({"error": result['message']}, status=429)
    except Account.DoesNotExist:
        pass # Enumeration protection
        
    return JsonResponse({"success": True, "message": "If the account exists, an OTP has been sent."})

def api_forgot_password_verify(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    data = json.loads(request.body)
    identifier = data.get('email', '').strip().lower()
    otp = data.get('otp')
    new_password = data.get('new_password')
    
    try:
        validate_password(new_password)
    except ValidationError as e:
        return JsonResponse({"error": e.messages[0]}, status=400)
        
    try:
        account = Account.objects.get(Q(email=identifier) | Q(username=identifier))
    except Account.DoesNotExist:
        return JsonResponse({"error": "Invalid request."}, status=400)

    result = services.verify_and_reset_password(account, otp, new_password)
    if not result['success']:
        return JsonResponse({"error": result['message']}, status=400)
        
    # Invalidate all active sessions for this user by updating their auth hash 
    update_session_auth_hash(request, account)
    
    return JsonResponse({"success": True, "message": result['message']})

def api_forgot_username_init(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    data = json.loads(request.body)
    email = data.get('email', '').strip().lower()
    
    try:
        account = Account.objects.get(email=email)
        result = services.initiate_username_recovery(account)
        if not result['success']:
             return JsonResponse({"error": result['message']}, status=429)
    except Account.DoesNotExist:
        pass # Enumeration protection
        
    return JsonResponse({"success": True, "message": "If the email matches our records, an OTP has been sent."})

def api_forgot_username_verify(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    data = json.loads(request.body)
    email = data.get('email', '').strip().lower()
    otp = data.get('otp')
    
    try:
        account = Account.objects.get(email=email)
        result = services.verify_and_send_username(account, otp)
        if not result['success']:
             return JsonResponse({"error": result['message']}, status=400)
        return JsonResponse({"success": True, "message": result['message']})
    except Account.DoesNotExist:
        return JsonResponse({"error": "Invalid request."}, status=400)

@transaction.atomic
def api_update_profile(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
        
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        account = request.user
        
        account.first_name = data.get('first_name', account.first_name)
        account.last_name = data.get('last_name', account.last_name)
        account.phone_number = data.get('phone_number', account.phone_number)
        
        new_password = data.get('new_password')
        if new_password:
            try:
                validate_password(new_password, account)
                account.set_password(new_password)
                update_session_auth_hash(request, account) # Invalidates other devices, keeps current device active
            except ValidationError as e:
                return JsonResponse({"error": e.messages[0]}, status=400)
                
        account.save()
        return JsonResponse({"success": True, "message": "Profile updated successfully."})
        
    except Exception as e:
        return JsonResponse({"error": "An error occurred while updating the profile."}, status=500)

@transaction.atomic
def api_delete_account(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
        
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    if request.user.role == Account.Role.ADMIN or request.user.is_superuser:
        return JsonResponse({"error": "Administrator accounts cannot be deleted via this endpoint."}, status=403)
        
    account = request.user
    logout(request)
    request.session.flush()
    account.delete()
    return JsonResponse({"success": True, "redirect_url": "/login/"})

#====================================================================================
#-------------------------END OF LOGIN AND SIGNUP------------------------------------------
#====================================================================================

@require_POST
def submit_review(request):
    try:
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        rating = int(request.POST.get('rating', 5))
        product_slug = request.POST.get('product_slug', 'anuradha-paithani-saree')
        product_name = request.POST.get('product_name', 'Anuradha Paithani Soft Peacock Design Saree')

        user = request.user if request.user.is_authenticated else None

        review = ProductReview.objects.create(
            user=user,
            product_slug=product_slug,
            product_name=product_name,
            title=title,
            comment=comment,
            rating=rating,
            image_1=request.FILES.get('image_1'),
            image_2=request.FILES.get('image_2'),
            image_3=request.FILES.get('image_3'),
            is_approved=True,
            is_verified_buyer=True
        )
        return JsonResponse({'success': True, 'message': 'Review submitted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def toggle_review_helpful(request, review_id):
    try:
        review = ProductReview.objects.get(id=review_id)
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key or 'guest'

        if user:
            created = ReviewHelpful.objects.get_or_create(review=review, user=user)[1]
        else:
            created = ReviewHelpful.objects.get_or_create(review=review, session_key=session_key)[1]

        if created:
            review.helpful_count += 1
            review.save()

        return JsonResponse({'success': True, 'helpful_count': review.helpful_count})
    except ProductReview.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)