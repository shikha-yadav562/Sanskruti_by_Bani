from django.urls import path
from . import views
app_name="adm_user"
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),

    # URLs for Categories
    path('categories/', views.categories, name='categories'),
    path("api/categories/", views.category_list_create, name="api_categories_list_create"),
    path('api/categories/<int:pk>/update/', views.category_update, name='api_categories_update'),
    path('api/categories/<int:pk>/delete/', views.category_delete, name='api_categories_delete'),

    # URLs for Filter
    path('filters/', views.filters, name='filters'),

    # ---- Colors ----
    path("filters/colors/", views.color_list_create, name="color_list_create"),
    path("filters/colors/<int:pk>/update/", views.color_update, name="color_update"),
    path("filters/colors/<int:pk>/delete/", views.color_delete, name="color_delete"),

    # ---- Fabrics ----
    path("filters/fabrics/", views.fabric_list_create, name="fabric_list_create"),
    path("filters/fabrics/<int:pk>/update/", views.fabric_update, name="fabric_update"),
    path("filters/fabrics/<int:pk>/delete/", views.fabric_delete, name="fabric_delete"),

    # ---- Prints ----
    path("filters/prints/", views.print_list_create, name="print_list_create"),
    path("filters/prints/<int:pk>/update/", views.print_update, name="print_update"),
    path("filters/prints/<int:pk>/delete/", views.print_delete, name="print_delete"),

    path('img_manager/', views.img_manager, name='img_manager'),
    path('coming_soon/', views.coming_soon, name='coming_soon'),
]