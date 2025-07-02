from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from users.models import Location


class Command(BaseCommand):
    help = 'Удаляет старые места'

    def handle(self, *args, **options):
        one_month_ago = timezone.now() - timedelta(days=30)
        old_locations = Location.objects.filter(created_at__lt=one_month_ago)
        count_deleted = len(old_locations)
        if count_deleted > 0:
            self.stdout.write(f'Удалено {count_deleted} старых мест.')
            old_locations.delete()
        else:
            self.stdout.write('Нет старых мест для удаления.')
