from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignupForm, LoginForm
from adm_user.models import AboutUsSection, HeroSlideOffer, HeroSlideMain, HeroSlideImageOnly, HeaderSettings, OfferBarItem, FooterSettings, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3

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


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            auth_login(request, user)
            return redirect('user:index')
    else:
        form = SignupForm()
    return render(request, 'user/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('adm_user:dashboard')
            return redirect('user:index')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'user/login.html')


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('user:login')


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