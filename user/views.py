
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, LoginForm
from adm_user.models import AboutUsSection, HeroSlideOffer, HeroSlideMain, HeroSlideImageOnly, HeaderSettings, OfferBarItem, FooterSettings, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3, SignatureCategoryItem

from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import render, get_object_or_404,  redirect
from django.core.serializers.json import DjangoJSONEncoder

from adm_user.models import (
    Product, ProductImage, SignatureCategoryItem, Color, Fabric, Print,Tag
)

# Create your views here.
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Address, ProductReview, ReviewHelpful

PRICE_BRACKETS = {
    "under-5000": (None, 5000),
    "5000-10000": (5000, 10000),
    "10000-20000": (10000, 20000),
    "above-20000": (20000, None),
}
price_choices = [
    ("under-5000", "Under ₹5,000"),
    ("5000-10000", "₹5,000 - ₹10,000"),
    ("10000-20000", "₹10,000 - ₹20,000"),
    ("above-20000", "Above ₹20,000"),
]

SORT_MAP = {
    "newest": "-created_at",
    "price-low": "base_price",
    "price-high": "-base_price",
}

# Create your views here.
def index(request):
    bestseller_qs = (
        Product.objects.filter(
            is_active=True,
            tags__slug="bestseller",
            category__slug="paithani",
        )
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("display_order", "created_at"),
                to_attr="all_images",
            )
        )
        .distinct()
        .order_by("-created_at")
    )
    bestseller_limit = 5 if bestseller_qs.count() < 10 else 10
    bestseller_products = bestseller_qs[:bestseller_limit]
    for product in bestseller_products:
        product.thumb = product.all_images[0] if product.all_images else None

    context = {
        "hero_offer": HeroSlideOffer.load(),
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
        "new_arrivals_tag": Tag.objects.filter(slug="new-arrival").first(),
        "bestsellers_tag": Tag.objects.filter(slug="bestseller").first(),
        "bestseller_products": bestseller_products,
    }
    return render(request, 'user/index.html', context)

def product(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'fabric', 'print_type'),
        slug=slug,
        is_active=True,
    )

    variants = (
        product.variants
        .filter(is_active=True)
        .select_related('color')
        .prefetch_related('images')
        .order_by('display_order')
    )

    default_images = product.images.filter(variant__isnull=True).order_by('display_order')

    # First active variant is the default selection on page load.
    default_variant = variants.first()
    if default_variant:
        gallery_images = default_variant.images.all() or default_images
        display_price = default_variant.price or product.final_price
    else:
        gallery_images = default_images
        display_price = product.final_price

    # Serialized for the color-swatch JS — swaps images/price/stock
    # client-side without a reload.
    variants_json = [
        {
            "variant_id": v.id,
            "color_name": v.color.name,
            "color_hex": v.color.hex_code,
            "price": str(v.price or product.final_price),
            "stock_quantity": v.stock_quantity,
            "images": [img.image_url for img in v.images.all()] or [img.image_url for img in default_images],
        }
        for v in variants
    ]

    reviews = ProductReview.objects.filter(product_slug=product.slug, is_approved=True)
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    avg_rating_formatted = round(avg_rating, 1)

    full_stars = int(avg_rating_formatted)
    has_half_star = (avg_rating_formatted - full_stars) >= 0.5

    star_counts = {n: reviews.filter(rating=n).count() for n in range(5, 0, -1)}
    star_percents = {
        n: round((c / total_reviews * 100)) if total_reviews > 0 else 0
        for n, c in star_counts.items()
    }

    customer_photos = []
    for r in reviews:
        if r.image_1: customer_photos.append(r.image_1)
        if r.image_2: customer_photos.append(r.image_2)
        if r.image_3: customer_photos.append(r.image_3)

    similar_products = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("display_order", "created_at"),
                to_attr="all_images",
            )
        )
        .order_by("-created_at")[:4]
    )
    for p in similar_products:
        default_imgs = [img for img in p.all_images if img.variant_id is None]
        p.thumb = default_imgs[0] if default_imgs else (p.all_images[0] if p.all_images else None)
    
    context = {
        "header_settings": HeaderSettings.load(),
        "footer_settings": FooterSettings.load(),
        "offer_items": OfferBarItem.objects.all(),
        "signature_categories": SignatureCategoryItem.objects.filter(is_active=True),
        "product": product,
        "variants": variants,
        "default_variant": default_variant,
        "gallery_images": gallery_images,
        "display_price": display_price,
        "variants_json": json.dumps(variants_json, cls=DjangoJSONEncoder),
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating_formatted,
        "full_stars": full_stars,
        "has_half_star": has_half_star,
        "star_counts": star_counts,
        "star_percents": star_percents,
        "customer_photos": customer_photos,
        "similar_products": similar_products,
        "new_arrivals_tag": Tag.objects.filter(slug="new-arrival").first(),
        "bestsellers_tag": Tag.objects.filter(slug="bestseller").first(),
    }
    return render(request, 'user/product.html', context)


def catalogue(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "fabric", "print_type")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.select_related("variant__color").order_by("display_order", "created_at"),
                to_attr="all_images",
            ),
            "variants__color",
        )
    )

    category_slugs = request.GET.getlist("category")
    fabric_slugs = request.GET.getlist("fabric")
    print_slugs = request.GET.getlist("print")
    color_slugs = request.GET.getlist("color")
    price_keys = request.GET.getlist("price")
    tag_slugs = request.GET.getlist("tag")

    if category_slugs:
        products = products.filter(category__slug__in=category_slugs)
    if fabric_slugs:
        products = products.filter(fabric__slug__in=fabric_slugs)
    if print_slugs:
        products = products.filter(print_type__slug__in=print_slugs)
    if color_slugs:
        products = products.filter(variants__color__slug__in=color_slugs).distinct()
    if tag_slugs:
        products = products.filter(tags__slug__in=tag_slugs).distinct()

    if price_keys:
        price_q = Q()
        for key in price_keys:
            lo, hi = PRICE_BRACKETS.get(key, (None, None))
            bracket = Q()
            if lo is not None:
                bracket &= Q(base_price__gte=lo)
            if hi is not None:
                bracket &= Q(base_price__lt=hi)
            price_q |= bracket
        products = products.filter(price_q)

    sort_key = request.GET.get("sort", "featured")
    if sort_key in SORT_MAP:
        products = products.order_by(SORT_MAP[sort_key])
    # "featured" keeps Product.Meta's default ordering (-created_at)

    paginator = Paginator(products, 5)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    querydict = request.GET.copy()
    querydict.pop("page", None)
    base_qs = querydict.urlencode()

    for product in page_obj.object_list:
        thumb = None
        if color_slugs:
            thumb = next(
                (img for img in product.all_images
                 if img.variant_id and img.variant.color.slug in color_slugs),
                None
            )
        if thumb is None:
            thumb = next((img for img in product.all_images if img.variant_id is None), None)
        if thumb is None and product.all_images:
            thumb = product.all_images[0]
        product.thumb = thumb

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "total_count": paginator.count,
        "price_choices": price_choices,

        "categories": SignatureCategoryItem.objects.filter(is_active=True),
        "colors": Color.objects.filter(is_active=True),
        "fabrics": Fabric.objects.filter(is_active=True),
        "prints": Print.objects.filter(is_active=True),
        "tags": Tag.objects.filter(),
        "new_arrivals_tag": Tag.objects.filter(slug="new-arrival").first(),
        "bestsellers_tag": Tag.objects.filter(slug="bestseller").first(),

        "selected_categories": category_slugs,
        "selected_fabrics": fabric_slugs,
        "selected_prints": print_slugs,
        "selected_colors": color_slugs,
        "selected_prices": price_keys,
        "selected_tags": tag_slugs,
        "current_sort": sort_key,
        "base_qs": base_qs,
    }
    return render(request, "user/catalogue.html", context)

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
from django.utils.http import url_has_allowed_host_and_scheme

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
        next_url = data.get('next', '').strip()
        
        account = authenticate(request, username=username, password=password)
        
        if account:
            login(request, account)
            request.session.cycle_key() # Session rotation
            
            if not remember_me:
                request.session.set_expiry(0) 
            else:
                request.session.set_expiry(30 * 24 * 60 * 60)
                
            services.log_login_attempt(request, account, "success", attempted_identifier=username)

            if account.role == 'admin':
                redirect_url = '/adm/'
            elif next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                redirect_url = next_url
            else:
                redirect_url = '/'

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
    next_url = data.get('next', '').strip()
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

    if account.role == 'admin':
        redirect_url = '/adm/'
    elif next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        redirect_url = next_url
    else:
        redirect_url = '/'

    return JsonResponse({"success": True, "redirect_url": redirect_url})

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

@login_required(login_url='user:login')
@require_POST
def submit_review(request):
    try:
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        rating = int(request.POST.get('rating', 5))
        product_slug = request.POST.get('product_slug', 'anuradha-paithani-saree')
        product_name = request.POST.get('product_name', 'Anuradha Paithani Soft Peacock Design Saree')

        review = ProductReview.objects.create(
            user=request.user,
            product_slug=product_slug,
            product_name=product_name,
            title=title,
            comment=comment,
            rating=rating,
            image_1=request.FILES.get('image_1'),
            image_2=request.FILES.get('image_2'),
            image_3=request.FILES.get('image_3'),
            is_approved=False,
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
    

#----------------------------SEARCH BAR----------------------------------------------------

from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import render

from adm_user.models import (
    Product,
    ProductImage,
    SignatureCategoryItem,
    Category,
    Color,
    Fabric,
    Print,
    Tag,
)


def search_suggest(request):
    q = request.GET.get("q", "").strip()

    # Don't search for very short queries
    if len(q) < 2:
        return JsonResponse({"results": []})

    products = (
        Product.objects
        .filter(is_active=True)
        .filter(
            Q(name__icontains=q)
            | Q(product_code__icontains=q)
            | Q(category__name__icontains=q)
        )
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects
                .select_related("variant__color")
                .order_by("display_order", "created_at"),
                to_attr="suggestion_images",
            )
        )[:6]
    )

    results = []

    for product in products:
        # Prefer the main/default product image
        thumb = next(
            (
                img
                for img in product.suggestion_images
                if img.variant_id is None
            ),
            None,
        )

        # Fallback to first available image
        if thumb is None and product.suggestion_images:
            thumb = product.suggestion_images[0]

        results.append(
            {
                "name": product.name,
                "slug": product.slug,
                "category": (
                    product.category.name
                    if product.category
                    else ""
                ),
                "price": float(
                    product.discount_price
                    if product.discount_price is not None
                    else product.base_price
                ),
                "thumbnail": (
                    thumb.image_url
                    if thumb
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "results": results,
            "query": q,
        }
    )


def catalogue(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "fabric", "print_type")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects
                .select_related("variant__color")
                .order_by("display_order", "created_at"),
                to_attr="all_images",
            ),
            "variants__color",
        )
    )

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------
    q = request.GET.get("q", "").strip()

    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(product_code__icontains=q)
            | Q(category__name__icontains=q)
        )

    # ---------------------------------------------------------
    # EXISTING FILTERS — KEPT AS-IS
    # ---------------------------------------------------------
    category_slugs = request.GET.getlist("category")
    fabric_slugs = request.GET.getlist("fabric")
    print_slugs = request.GET.getlist("print")
    color_slugs = request.GET.getlist("color")
    price_keys = request.GET.getlist("price")
    tag_slugs = request.GET.getlist("tag")

    if category_slugs:
        products = products.filter(
            category__slug__in=category_slugs
        )

    if fabric_slugs:
        products = products.filter(
            fabric__slug__in=fabric_slugs
        )

    if print_slugs:
        products = products.filter(
            print_type__slug__in=print_slugs
        )

    if color_slugs:
        products = products.filter(
            variants__color__slug__in=color_slugs
        ).distinct()

    if tag_slugs:
        products = products.filter(
            tags__slug__in=tag_slugs
        ).distinct()

    # ---------------------------------------------------------
    # EXISTING PRICE FILTER — KEPT AS-IS
    # ---------------------------------------------------------
    if price_keys:
        price_q = Q()

        for key in price_keys:
            lo, hi = PRICE_BRACKETS.get(
                key,
                (None, None)
            )

            bracket = Q()

            if lo is not None:
                bracket &= Q(base_price__gte=lo)

            if hi is not None:
                bracket &= Q(base_price__lt=hi)

            price_q |= bracket

        products = products.filter(price_q)

    # ---------------------------------------------------------
    # EXISTING SORTING — KEPT AS-IS
    # ---------------------------------------------------------
    sort_key = request.GET.get("sort", "featured")

    if sort_key in SORT_MAP:
        products = products.order_by(
            SORT_MAP[sort_key]
        )

    # "featured" keeps Product.Meta's default ordering
    # (-created_at)

    # ---------------------------------------------------------
    # PAGINATION — KEPT AS-IS
    # ---------------------------------------------------------
    paginator = Paginator(products, 5)

    page_obj = paginator.get_page(
        request.GET.get("page", 1)
    )

    # ---------------------------------------------------------
    # KEEP SEARCH + FILTERS + SORT WHEN PAGINATING
    # ---------------------------------------------------------
    querydict = request.GET.copy()
    querydict.pop("page", None)

    base_qs = querydict.urlencode()

    # ---------------------------------------------------------
    # EXISTING COLOR-SPECIFIC THUMBNAIL LOGIC — KEPT AS-IS
    # ---------------------------------------------------------
    for product in page_obj.object_list:
        thumb = None

        if color_slugs:
            thumb = next(
                (
                    img
                    for img in product.all_images
                    if img.variant_id
                    and img.variant.color.slug in color_slugs
                ),
                None,
            )

        if thumb is None:
            thumb = next(
                (
                    img
                    for img in product.all_images
                    if img.variant_id is None
                ),
                None,
            )

        if thumb is None and product.all_images:
            thumb = product.all_images[0]

        product.thumb = thumb

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------
    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "total_count": paginator.count,

        "price_choices": price_choices,

        "categories": SignatureCategoryItem.objects.filter(
            is_active=True
        ),

        "colors": Color.objects.filter(
            is_active=True
        ),

        "fabrics": Fabric.objects.filter(
            is_active=True
        ),

        "prints": Print.objects.filter(
            is_active=True
        ),

        "tags": Tag.objects.all(),

        "new_arrivals_tag": Tag.objects.filter(
            slug="new-arrival"
        ).first(),

        "bestsellers_tag": Tag.objects.filter(
            slug="bestseller"
        ).first(),

        "selected_categories": category_slugs,
        "selected_fabrics": fabric_slugs,
        "selected_prints": print_slugs,
        "selected_colors": color_slugs,
        "selected_prices": price_keys,
        "selected_tags": tag_slugs,

        "current_sort": sort_key,

        # NEW: search query for the template
        "query": q,

        # Preserves q + filters + sort during pagination
        "base_qs": base_qs,
    }

    return render(
        request,
        "user/catalogue.html",
        context
    )
    
    #--------------------------WHATSAPP REDIRECT BUY--------------------------------------
    
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import quote
@login_required(login_url='user:login')
def buy_now(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)

    display_price = product.final_price
    variant_id = request.GET.get('variant')
    if variant_id:
        variant = (
            product.variants
            .filter(id=variant_id, is_active=True)
            .select_related('color')
            .first()
        )
        if variant and variant.price:
            display_price = variant.price

    product_url = f"{request.scheme}://{request.get_host()}{reverse('user:product', args=[product.slug])}"
    message = (
        f"Hi, I am interested in {product.name}. "
        f"Price: ₹{int(display_price)}. "
        f"Product Link: {product_url}"
    )
    return redirect(f"https://wa.me/7900152351?text={quote(message)}")