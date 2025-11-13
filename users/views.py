from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from mailings.models import MailingAttempt

from .forms import EmailAuthenticationForm, UserProfileForm, UserRegistrationForm
from .models import User


class UserLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "users/login.html"


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("mailings:home")


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        form.save_m2m()
        messages.success(self.request, "Регистрация завершена. Вы можете войти.")
        return super().form_valid(form)


class RegistrationDoneView(TemplateView):
    template_name = "users/registration_done.html"


class ConfirmEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            messages.success(
                request, "Email успешно подтвержден. Теперь вы можете войти."
            )
            return redirect("users:login")

        messages.error(request, "Некорректная ссылка подтверждения.")
        return redirect("mailings:home")


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)
        context.update(
            {
                "mailings_count": self.request.user.mailings.count(),
                "messages_count": self.request.user.messages.count(),
                "recipients_count": self.request.user.recipients.count(),
                "attempts_success": attempts.filter(
                    status=MailingAttempt.STATUS_SUCCESS
                ).count(),
                "attempts_failed": attempts.filter(
                    status=MailingAttempt.STATUS_FAILED
                ).count(),
                "attempts_total": attempts.count(),
            }
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлен.")
        return super().form_valid(form)


class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    permission_required = "users.view_user"


class UserBlockView(PermissionRequiredMixin, View):
    permission_required = "users.change_user"

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"Пользователь {user.email} заблокирован.")
        return redirect("users:user_list")
