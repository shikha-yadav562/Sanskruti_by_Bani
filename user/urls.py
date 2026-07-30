from django.urls import path
from . import views
app_name="user"

urlpatterns = [
    path('', views.index, name='index'),
    path('product/', views.product, name='product'),
    path('catalogue/', views.catalogue, name='catalogue'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]