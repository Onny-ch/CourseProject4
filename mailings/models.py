from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Recipient(models.Model):
    email = models.EmailField("Email", unique=True)
    full_name = models.CharField("Ф. И. О.", max_length=255)
    comment = models.TextField("Комментарий", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        permissions = [
            (
                "can_view_all_recipients",
                "Может просматривать всех получателей рассылки",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField("Тема письма", max_length=255)
    body = models.TextField("Тело письма", validators=[MinLengthValidator(1)])
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        permissions = [
            ("can_view_all_messages", "Может просматривать все сообщения"),
        ]

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    )

    start_at = models.DateTimeField("Дата и время первой отправки")
    end_at = models.DateTimeField("Дата и время окончания отправки")
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Recipient, related_name="mailings", verbose_name="Получатели"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        permissions = [
            ("can_view_all_mailings", "Может просматривать все рассылки"),
            ("can_disable_mailings", "Может отключать рассылки"),
        ]

    def __str__(self):
        return f"Рассылка #{self.pk}"

    def mark_running(self):
        if self.status != self.STATUS_RUNNING:
            self.status = self.STATUS_RUNNING
            self.save(update_fields=["status"])

    def mark_completed(self):
        if self.status != self.STATUS_COMPLETED:
            self.status = self.STATUS_COMPLETED
            self.save(update_fields=["status"])


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    )

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Получатель",
    )
    attempted_at = models.DateTimeField("Дата и время попытки", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES)
    server_response = models.TextField("Ответ почтового сервера", blank=True)

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempted_at",)

    def __str__(self):
        return f"Попытка {self.get_status_display()} для {self.mailing}"
