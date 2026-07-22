from django.urls import path
from . import views
app_name="adm_user"
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
    path('categories/', views.categories, name='categories'),
    path("api/categories/", views.category_list_create, name="api_categories_list_create"),
    # path("api/categories/<int:pk>/", views.category_detail, name="api_categories_detail"),
    path('api/categories/<int:pk>/update/', views.category_update, name='api_categories_update'),
    path('api/categories/<int:pk>/delete/', views.category_delete, name='api_categories_delete'),
    path('filters/', views.filters, name='filters'),
    path('img_manager/', views.img_manager, name='img_manager'),
    path('coming_soon/', views.coming_soon, name='coming_soon'),
]