from django.urls import path
from . import views
app_name="adm_user"
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
    path('categories/', views.categories, name='categories'),
    path('filters/', views.filters, name='filters'),
    path('img_manager/', views.img_manager, name='img_manager'),
    path('coming_soon/', views.coming_soon, name='coming_soon'),
]