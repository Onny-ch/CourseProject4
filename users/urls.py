from django.urls import path

from .views import (
    ConfirmEmailView,
    ProfileUpdateView,
    ProfileView,
    RegisterView,
    RegistrationDoneView,
    UserBlockView,
    UserListView,
    UserLoginView,
    UserLogoutView,
)

app_name = "users"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("register/done/", RegistrationDoneView.as_view(), name="registration_done"),
    path("confirm/<uidb64>/<token>/", ConfirmEmailView.as_view(), name="confirm_email"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/block/", UserBlockView.as_view(), name="user_block"),
]
