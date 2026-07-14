from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'user/index.html')

def product(request):
    return render(request, 'user/product.html')

def catalogue(request):
    return render(request, 'user/catalogue.html')