# /management/commands/import_group_roles.py
# python manage.py import_group_roles --file downloads/group_roles.json
# python manage.py import_group_roles --file downloads/group_roles.json --dry-run

from django.core.management.base import BaseCommand
from users.models import GroupRoles
import json

class Command(BaseCommand):
    help = 'Импортирует записи модели GroupRoles из файла.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, type=str, help='Имя файла с данными для импорта.')
        parser.add_argument('--dry-run', action='store_true', help='Проверяет операцию импорта без фактического изменения базы данных.')

    def handle(self, *args, **options):
        input_file = options['file']
        dry_run = options['dry_run']
        changes_count = 0

        try:
            with open(input_file, 'r',encoding='utf-8') as file:
                data = json.load(file)

            for item in data:
                name = item['name']
                description = item['description']
                roles = item['roles']

                existing_obj = GroupRoles.objects.filter(name=name).first()

                if existing_obj:
                    update_fields = {}
                    if existing_obj.description != description:
                        update_fields['description'] = description
                    if existing_obj.roles != roles:
                        update_fields['roles'] = roles

                    if update_fields:
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'Обнаружены изменения для объекта "{name}": {update_fields}.'))
                        else:
                            GroupRoles.objects.filter(name=name).update(**update_fields)
                            changes_count += 1
                else:
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f'Будет создано новое объект с названием "{name}".'))
                    else:
                        new_obj = GroupRoles.objects.create(name=name, description=description, roles=roles)
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