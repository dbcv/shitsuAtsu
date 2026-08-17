# myq/account_urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views.setting import setting_view
from .views.views import SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("setting/", setting_view, name="setting"),
    path("login/", LoginView.as_view(template_name="myq/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
]
