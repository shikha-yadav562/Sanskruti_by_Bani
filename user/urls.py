from django.urls import path
from . import views
app_name="user"

urlpatterns = [
    path('', views.index, name='index'),
    path('product/', views.product, name='product'),
    path('catalogue/', views.catalogue, name='catalogue'),
]