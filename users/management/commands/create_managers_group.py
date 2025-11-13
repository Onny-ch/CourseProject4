from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создает или обновляет группу 'Менеджеры' с необходимыми правами"

    PERMISSIONS = (
        "users.view_user",
        "users.change_user",
        "mailings.can_view_all_mailings",
        "mailings.can_disable_mailings",
        "mailings.can_view_all_messages",
        "mailings.can_view_all_recipients",
        "mailings.view_mailing",
        "mailings.view_message",
        "mailings.view_recipient",
        "mailings.view_mailingattempt",
    )

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Менеджеры")
        for perm in self.PERMISSIONS:
            app_label, codename = perm.split(".")
            permission = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            if permission:
                group.permissions.add(permission)
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджеры' создана"))
        else:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджеры' обновлена"))
