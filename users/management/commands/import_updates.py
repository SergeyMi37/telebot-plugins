# /management/commands/export_group_roles.py
# python manage.py export_options --file downloads/optiions.json

from django.core.management.base import BaseCommand
from users.models import Updates
import json


class Command(BaseCommand):
    help = 'Импортирует записи модели Updates из файла.'

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
                update_id = item['update_id']
                message = item['message']
                from_id = item['from_id']
                chat_id = item['chat_id']
                json_field = item['json']

                existing_obj = Updates.objects.filter(update_id=update_id).first()

                if existing_obj:
                    update_fields = {}
                    if existing_obj.message != message:
                        update_fields['message'] = message
                    if existing_obj.from_id != from_id:
                        update_fields['from_id'] = from_id
                    if existing_obj.chat_id != chat_id:
                        update_fields['chat_id'] = chat_id
                    if existing_obj.json != json_field:
                        update_fields['json'] = json_field

                    if update_fields:
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'Обнаружены изменения для объекта с id={update_id}: {update_fields}.'))
                        else:
                            Updates.objects.filter(update_id=update_id).update(**update_fields)
                            changes_count += 1
                else:
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f'Будет создано новое объект с id="{update_id}".'))
                    else:
                        new_obj = Updates.objects.create(
                            update_id=update_id,
                            message=message,
                            from_id=from_id,
                            chat_id=chat_id,
                            json=json_field
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