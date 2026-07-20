from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'adm_user/index.html')

def dashboard(request):
    return render(request, 'adm_user/dashboard.html')

def products(request):
    return render(request, 'adm_user/products.html')

def categories(request):
    return render(request, 'adm_user/categories.html')

def filters(request):
    return render(request, 'adm_user/filters.html')

def img_manager(request):
    return render(request, 'adm_user/image_manager.html')

def coming_soon(request):
    return render(request, 'adm_user/coming-soon.html')