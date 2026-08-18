from django.urls import path
from . import views
app_name="adm_user"
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.dashboard, name='dashboard'),
    

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

    # ---- Tags ----
    path("filters/tags/", views.tag_list_create, name="tag_list_create"),
    path("filters/tags/<int:pk>/update/", views.tag_update, name="tag_update"),
    path("filters/tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),

    # ---- Products ----
    path('products/', views.products, name='products'),
    path("product/add/", views.product_create, name="create"),
    path("product/<slug:slug>/edit/", views.product_update, name="update"),
    path("product/<slug:slug>/delete/", views.product_delete, name="delete"),
    path('product/<slug:slug>/', views.product_detail, name='detail'),

    path('products/export/', views.products_export, name='products_export'),
    path('products/<slug:slug>/stock/', views.product_stock_update, name='product_stock_update'),

    path('img_manager/', views.img_manager, name='img_manager'),
    path('website-builder/', views.website_builder, name='website_builder'),
    path('coming_soon/', views.coming_soon, name='coming_soon'),
    
    #------ Website Builder -------
    

 
    # Singleton section saves — one per sidebar tab
     path("website-builder/", views.website_builder, name="website_builder"),
 
    # Singleton section saves
    path("website-builder/save/hero-main/", views.save_hero_main, name="save_hero_main"),
    path("website-builder/save/hero-image-only/", views.save_hero_image_only, name="save_hero_image_only"),
    path("website-builder/save/hero-offer/", views.save_hero_offer, name="save_hero_offer"),
    path("website-builder/save/memories/", views.save_memories_section, name="save_memories_section"),
    path("website-builder/save/memories-offer-slide/", views.save_memories_offer_slide, name="save_memories_offer_slide"),
    path("website-builder/save/memories-slide3/", views.save_memories_slide3, name="save_memories_slide3"),
    path("website-builder/save/header/", views.save_header_settings, name="save_header_settings"),
    path("website-builder/save/footer/", views.save_footer_settings, name="save_footer_settings"),
    path("website-builder/save/about/", views.save_about_section, name="save_about_section"),
 
    # Offer bar items (dynamic list)
    path("website-builder/offer-items/", views.offer_items, name="offer_items"),
    path("website-builder/offer-items/<int:pk>/", views.offer_item_delete, name="offer_item_delete"),
 
    # Memory gallery (dynamic list)
    path("website-builder/memory-images/", views.memory_images, name="memory_images"),
    path("website-builder/memory-images/<int:pk>/", views.memory_image_delete, name="memory_image_delete"),
    path("website-builder/memory-images/reorder/", views.memory_images_reorder, name="memory_images_reorder"),

    # Signature Categories management (5 Signature Saree Categories)
    path("website-builder/signature-categories/", views.signature_categories_api, name="signature_categories_api"),
    path("website-builder/signature-categories/<int:pk>/edit/", views.signature_category_edit, name="signature_category_edit"),
    path("website-builder/signature-categories/<int:pk>/delete/", views.signature_category_delete, name="signature_category_delete"),

    # Customer Reviews Management
    path("reviews/", views.reviews_management, name="reviews_management"),
    path("reviews/approve/<int:pk>/", views.approve_review, name="approve_review"),
    path("reviews/delete/<int:pk>/", views.delete_review, name="delete_review"),

]