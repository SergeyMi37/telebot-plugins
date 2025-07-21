# /management/commands/import_options.py
# python manage.py import_options --file downloads/options.json
# python manage.py import_options --file downloads/options.json --dry-run

from django.core.management.base import BaseCommand
from users.models import Options
import json

class Command(BaseCommand):
    help = 'Импортирует записи модели Options из файла.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, type=str, help='Имя файла с данными для импорта.')
        parser.add_argument('--dry-run', action='store_true', help='Проверяет операцию импорта без фактического изменения базы данных.')

    def handle(self, *args, **options):
        input_file = options['file']
        dry_run = options['dry_run']
        changes_count = 0

        try:
            with open(input_file, 'r') as file:
                data = json.load(file)

            for item in data:
                name = item['name']
                description = item['description']
                category = item['category']
                option_type = item['type']
                value = item['value']
                roles = item['roles']
                enabled = item['enabled']

                existing_obj = Options.objects.filter(name=name).first()

                if existing_obj:
                    update_fields = {}
                    if existing_obj.description != description:
                        update_fields['description'] = description
                    if existing_obj.category != category:
                        update_fields['category'] = category
                    if existing_obj.type != option_type:
                        update_fields['type'] = option_type
                    if existing_obj.value != value:
                        update_fields['value'] = value
                    if existing_obj.roles != roles:
                        update_fields['roles'] = roles
                    if existing_obj.enabled != enabled:
                        update_fields['enabled'] = enabled

                    if update_fields:
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'Обнаружены изменения для объекта "{name}": {update_fields}.'))
                        else:
                            Options.objects.filter(name=name).update(**update_fields)
                            changes_count += 1
                else:
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f'Будет создано новое объект с названием "{name}".'))
                    else:
                        new_obj = Options.objects.create(
                            name=name,
                            description=description,
                            category=category,
                            type=option_type,
                            value=value,
                            roles=roles,
                            enabled=enabled
                        )
                        changes_count += 1

            if dry_run:
                self.stdout.write(self.style.NOTICE('Операция выполнена в режиме проверки ("dry run"). Никаких изменений в базе данных не произошло.'))
            elif changes_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Успешно выполнено: всего изменено / создано {changes_count} объектов.'))
            else:
                self.stdout.write(self.style.SUCCESS('Нет изменений в базе данных.'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Файл "{input_file}" не найден.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка при импорте данных: {e}'))