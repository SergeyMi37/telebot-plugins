# /management/commands/export_group_roles.py
# python manage.py imp_exp_updates --file downloads/updates.json

from users.models import Updates
from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q
from django.apps import apps
import json
import os


class Command(BaseCommand):
    help = 'Импортирует или экспортирует объекты модели Updates'

    def add_arguments(self, parser):
        parser.add_argument('--import', type=int, default=0,
                            help='1 для импорта, иначе экспорт')
        parser.add_argument('--file', required=True,
                            help='Путь к файлу для экспорта или импорта.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Проверка операции без изменения базы данных (только для импорта)')

    def handle(self, *args, **options):
        file_path = options['file']
        is_import = bool(options['import'])
        dry_run = options['dry_run'] # (дефис заменяется на подчеркивание) автоматически парсером argparse. Поэтому правильный доступ к параметру должен выглядеть так:

        if not os.path.exists(file_path) and is_import:
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return

        print(apps.all_models)
        model_class = apps.get_model('users', 'updates')  # Подставьте ваше приложение и название модели

        if is_import:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            total_count = len(data)
            imported_count = 0
            for item in data:
                try:
                    obj = model_class(**item)
                    
                    if dry_run:
                        continue
                        
                    obj.save()
                    imported_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Ошибка импорта записи: {e}'))
                
            result_message = f'Импортировано {imported_count}/{total_count}'
        
        else:
            updates = list(model_class.objects.all().values())
            with open(file_path, 'w') as f:
                json.dump(updates, f, indent=4)
            result_message = f'Экспорт успешно выполнен в файл {file_path}. Всего записей: {len(updates)}'

        self.stdout.write(result_message)