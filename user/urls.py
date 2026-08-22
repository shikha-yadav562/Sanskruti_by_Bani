from django.urls import path
from . import views
app_name="user"

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<slug:slug>/', views.product, name='product'),
    path('catalogue/', views.catalogue, name='catalogue'),
    path('profile/', views.profile_view, name='profile'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('return-refund-policy/', views.return_refund_policy, name='return_refund_policy'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    # path('login/', views.login_view, name='login'),
    # path('signup/', views.signup_view, name='signup'),
    # path('logout/', views.logout_view, name='logout'),
    path('review/submit/', views.submit_review, name='submit_review'),
    path('review/helpful/<int:review_id>/', views.toggle_review_helpful, name='toggle_review_helpful'),

    
    
    #---------------LOGIN AND SIGNUP-------------
    # Pages
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    
    # API Endpoints
    path('api/auth/login/', views.api_login, name='api_login'),
    path('api/auth/logout/', views.api_logout, name='api_logout'),
    path('api/auth/signup/init/', views.api_signup_init, name='api_signup_init'),
    path('api/auth/signup/verify/', views.api_signup_verify, name='api_signup_verify'),
    path('api/auth/password/forgot/', views.api_forgot_password_init, name='api_forgot_password'),
    path('api/auth/password/reset/', views.api_forgot_password_verify, name='api_reset_password'),
    path('api/auth/username/forgot/', views.api_forgot_username_init, name='api_forgot_username_init'),
    path('api/auth/username/verify/', views.api_forgot_username_verify, name='api_forgot_username_verify'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/profile/delete/', views.api_delete_account, name='api_delete_account'),
]