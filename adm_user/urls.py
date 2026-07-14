from django.urls import path
from . import views
app_name="adm_user"
urlpatterns = [
    path('', views.index, name='index'),
]