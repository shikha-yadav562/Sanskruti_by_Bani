from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignupForm, LoginForm
from adm_user.models import AboutUsSection, HeroSlideOffer, HeroSlideMain, HeroSlideImageOnly, HeaderSettings, OfferBarItem, FooterSettings, SweetMemoriesSection, SweetMemoryImage

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
    }
    return render(request, 'user/index.html', context)

def product(request):
    return render(request, 'user/product.html')

def catalogue(request):
    return render(request, 'user/catalogue.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            auth_login(request, user)
            return redirect('user:dashboard')
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
            return redirect('user:dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'user/login.html')


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('user:login')