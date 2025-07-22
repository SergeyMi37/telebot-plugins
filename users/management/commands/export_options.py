# /management/commands/export_group_roles.py
# python manage.py export_options --file downloads/optiions.json

from django.core.management.base import BaseCommand
from users.models import Options
import json

class Command(BaseCommand):
    help = 'Экспортирует все записи модели Options в файл.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, type=str, help='Имя файла для сохранения экспортируемых записей.')

    def handle(self, *args, **options):
        output_file = options['file']
        data = []
        for obj in Options.objects.all():
            record = {
                'name': obj.name,
                'description': obj.description,
                'category': obj.category,
                'type': obj.type,
                'value': obj.value,
                'roles': obj.roles,
                'enabled': obj.enabled
            }
            data.append(record)
        
        with open(output_file, 'w',encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False,encoding="utf-8")
        
        self.stdout.write(self.style.SUCCESS(f'Данные успешно экспортированы в файл "{output_file}".'))