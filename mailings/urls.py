from django.urls import path

from .views import (
    HomeView,
    MailingAttemptListView,
    MailingCreateView,
    MailingDeleteView,
    MailingDetailView,
    MailingDisableView,
    MailingListView,
    MailingSendView,
    MailingUpdateView,
    MessageCreateView,
    MessageDeleteView,
    MessageListView,
    MessageUpdateView,
    RecipientCreateView,
    RecipientDeleteView,
    RecipientListView,
    RecipientUpdateView,
)

app_name = "mailings"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("recipients/", RecipientListView.as_view(), name="recipient_list"),
    path("recipients/create/", RecipientCreateView.as_view(), name="recipient_create"),
    path(
        "recipients/<int:pk>/edit/",
        RecipientUpdateView.as_view(),
        name="recipient_update",
    ),
    path(
        "recipients/<int:pk>/delete/",
        RecipientDeleteView.as_view(),
        name="recipient_delete",
    ),
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/create/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/edit/", MessageUpdateView.as_view(), name="message_update"),
    path(
        "messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"
    ),
    path("mailings/", MailingListView.as_view(), name="mailing_list"),
    path("mailings/create/", MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/edit/", MailingUpdateView.as_view(), name="mailing_update"),
    path(
        "mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailing_delete"
    ),
    path("mailings/<int:pk>/send/", MailingSendView.as_view(), name="mailing_send"),
    path(
        "mailings/<int:pk>/disable/",
        MailingDisableView.as_view(),
        name="mailing_disable",
    ),
    path("attempts/", MailingAttemptListView.as_view(), name="attempt_list"),
]
