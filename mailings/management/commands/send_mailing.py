from django.core.management.base import BaseCommand, CommandError

from mailings.models import Mailing
from mailings.services import MailingSender


class Command(BaseCommand):
    help = "Отправить рассылку по идентификатору"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist as exc:
            raise CommandError(f"Рассылка с id={mailing_id} не найдена") from exc

        sender = MailingSender(mailing)
        attempts = sender.send()
        self.stdout.write(self.style.SUCCESS(f"Создано {attempts} попыток отправки"))
