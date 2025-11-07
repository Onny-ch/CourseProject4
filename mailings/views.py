from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, MailingAttempt, Message, Recipient
from .services import MailingSender


@method_decorator(cache_page(60), name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_mailings": Mailing.objects.count(),
                "active_mailings": Mailing.objects.filter(
                    status=Mailing.STATUS_RUNNING
                ).count(),
                "unique_recipients": Recipient.objects.values("email")
                .distinct()
                .count(),
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response.headers["Cache-Control"] = "public, max-age=60"
        return response


class OwnerProtectedQuerysetMixin:
    model = None
    permission_name = None

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.has_perm(self.permission_name):
            return qs
        return qs.filter(owner=user)


class RecipientListView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, ListView):
    model = Recipient
    template_name = "mailings/recipient_list.html"
    permission_name = "mailings.can_view_all_recipients"
    context_object_name = "recipients"


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("mailings:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Получатель создан")
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("mailings:recipient_list")
    permission_name = "mailings.can_view_all_recipients"

    def form_valid(self, form):
        messages.success(self.request, "Получатель обновлен")
        return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, DeleteView):
    model = Recipient
    template_name = "mailings/confirm_delete.html"
    success_url = reverse_lazy("mailings:recipient_list")
    permission_name = "mailings.can_view_all_recipients"


class MessageListView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, ListView):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "messages"
    permission_name = "mailings.can_view_all_messages"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Сообщение создано")
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")
    permission_name = "mailings.can_view_all_messages"

    def form_valid(self, form):
        messages.success(self.request, "Сообщение обновлено")
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, DeleteView):
    model = Message
    template_name = "mailings/confirm_delete.html"
    success_url = reverse_lazy("mailings:message_list")
    permission_name = "mailings.can_view_all_messages"


class MailingListView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"
    permission_name = "mailings.can_view_all_mailings"


class MailingDetailView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, DetailView):
    model = Mailing
    template_name = "mailings/mailing_detail.html"
    permission_name = "mailings.can_view_all_mailings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = self.object.attempts.all()
        context["successful_attempts"] = attempts.filter(
            status=MailingAttempt.STATUS_SUCCESS
        ).count()
        context["failed_attempts"] = attempts.filter(
            status=MailingAttempt.STATUS_FAILED
        ).count()
        context["total_attempts"] = attempts.count()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Рассылка создана")
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")
    permission_name = "mailings.can_view_all_mailings"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Рассылка обновлена")
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, OwnerProtectedQuerysetMixin, DeleteView):
    model = Mailing
    template_name = "mailings/confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")
    permission_name = "mailings.can_view_all_mailings"


class MailingSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        if mailing.owner != request.user and not request.user.has_perm(
            "mailings.can_view_all_mailings"
        ):
            return HttpResponseForbidden()

        sender = MailingSender(mailing)
        attempts = sender.send()
        messages.info(request, f"Запущено {attempts} попыток отправки")
        return redirect("mailings:mailing_detail", pk=pk)


class MailingDisableView(PermissionRequiredMixin, View):
    permission_required = "mailings.can_disable_mailings"

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = Mailing.STATUS_COMPLETED
        mailing.end_at = now()
        mailing.save(update_fields=["status", "end_at"])
        messages.success(request, "Рассылка отключена")
        return redirect("mailings:mailing_detail", pk=pk)


class MailingAttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = "mailings/attempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        qs = super().get_queryset().select_related("mailing", "recipient")
        user = self.request.user
        if user.has_perm("mailings.can_view_all_mailings"):
            return qs
        return qs.filter(mailing__owner=user)
