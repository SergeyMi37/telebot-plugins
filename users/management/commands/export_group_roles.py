# /management/commands/export_group_roles.py
# python manage.py export_group_roles --file downloads/group_roles.json

from django.core.management.base import BaseCommand
from users.models import GroupRoles
import json

class Command(BaseCommand):
    help = 'Экспортирует все записи модели GroupRoles в файл.'
    
    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, type=str, help='Имя файла для сохранения экспортируемых записей.')

    def handle(self, *args, **options):
        output_file = options['file']
        data = []
        for obj in GroupRoles.objects.all():
            record = {
                'name': obj.name,
                'description': obj.description,
                'roles': obj.roles
            }
            data.append(record)
        
        with open(output_file, 'w',encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'Данные успешно экспортированы в файл "{output_file}".'))
