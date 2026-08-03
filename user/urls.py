from django.urls import path
from . import views
app_name="user"

urlpatterns = [
    path('', views.index, name='index'),
    path('product/', views.product, name='product'),
    path('catalogue/', views.catalogue, name='catalogue'),
    path('profile/', views.profile_view, name='profile'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('return-refund-policy/', views.return_refund_policy, name='return_refund_policy'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('review/submit/', views.submit_review, name='submit_review'),
    path('review/helpful/<int:review_id>/', views.toggle_review_helpful, name='toggle_review_helpful'),
]