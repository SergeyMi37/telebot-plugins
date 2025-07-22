# /management/commands/export_group_roles.py
# python manage.py export_updates --file downloads/updates.json

from django.core.management.base import BaseCommand
from users.models import Updates
import json


class Command(BaseCommand):
    help = 'Экспортирует все записи модели Updates в файл.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, type=str, help='Имя файла для сохранения экспортируемых записей.')

    def handle(self, *args, **options):
        output_file = options['file']
        data = []
        for obj in Updates.objects.all():
            record = {
                'update_id': obj.update_id,
                'message': obj.message,
                'from_id': obj.from_id,
                'chat_id': obj.chat_id,
                'json': obj.json
            }
            data.append(record)
        
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'Данные успешно экспортированы в файл "{output_file}".'))