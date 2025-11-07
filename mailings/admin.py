from django.contrib import admin

from .models import Mailing, MailingAttempt, Message, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "owner")
    search_fields = ("email", "full_name")
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner")
    search_fields = ("subject", "body")
    list_filter = ("owner",)


class RecipientInline(admin.TabularInline):
    model = Mailing.recipients.through
    extra = 0


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_at", "end_at", "status", "owner")
    list_filter = ("status", "owner")
    search_fields = ("message__subject",)
    filter_horizontal = ("recipients",)
    inlines = [RecipientInline]


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "recipient", "attempted_at", "status")
    list_filter = ("status", "attempted_at")
    search_fields = ("recipient__email", "mailing__message__subject")
