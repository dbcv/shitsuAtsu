# myq/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views.views import SignUpView
from .views.setting import setting_view

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('setting/', setting_view, name='setting'),
    path('login/', LoginView.as_view(template_name='myq/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]