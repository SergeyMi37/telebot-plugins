from django.core.management.base import BaseCommand
from import_export.resources import modelresource_factory
from import_export.formats import base_formats
from importlib import import_module
import sys
import traceback


class Command(BaseCommand):
    help = 'Команда для импорта и экспорта моделей Django.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--import', dest='is_import', type=int, choices=[0, 1], default=0,
            help='Операция: 1 - импортировать, 0 - экспортировать.'
        )
        parser.add_argument(
            '--model', dest='model_name', required=True,
            help='Имя модели (например, User или Product).'
        )
        parser.add_argument(
            '--file', dest='file_path', required=True,
            help='Путь к файлу для экспорта или импорта.'
        )
        parser.add_argument(
            '--format', dest='file_format', default='csv',
            help='Формат файла (csv, xlsx, json). По умолчанию csv.'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Выполнить проверку операции без внесения изменений в базу данных (только для импорта).'
        )

    def handle(self, *args, **options):
        from django.conf import settings
        from django.contrib.admin.sites import site
        from django.core.exceptions import ImproperlyConfigured

        is_import = bool(options['is_import'])
        model_name = options['model_name']
        file_path = options['file_path']
        format_type = options['file_format'].lower()
        dry_run = options['dry_run']

        # Получаем модель из настроек проекта
        try:
            ModelClass = getattr(sys.modules[f'{settings.PROJECT_NAME}.{settings.MODELS_MODULE}'], model_name)
        except AttributeError:
            raise ImproperlyConfigured(f'Модель {model_name} не найдена!')

        resource_class = modelresource_factory(ModelClass)()

        formats_map = {
            'csv': base_formats.CSV(),
            'xlsx': base_formats.XLSX(),
            'json': base_formats.JSON(),
        }

        selected_format = formats_map.get(format_type)
        if not selected_format:
            raise ValueError(f'Неподдерживаемый формат файла: {format_type}')

        if is_import:
            dataset = selected_format.create_dataset(open(file_path, 'rb').read())
            result = resource_class.import_data(dataset, dry_run=dry_run)

            if dry_run:
                self.stdout.write(self.style.WARNING(f'Импорт прошел бы успешно, было бы обновлено/добавлено: {result.totals["new"] + result.totals["updated"]}, ошибок: {result.totals["errors"]}.'))
            elif result.has_errors():
                self.stdout.write(self.style.ERROR('При импорте возникли ошибки:'))
                for row_num, error_list in result.row_errors():
                    self.stdout.write(f'Строка {row_num}: {" ".join([f"{col}({type(e).__name__})" for col, e in error_list])}')
            else:
                self.stdout.write(self.style.SUCCESS(f'Импорт завершен успешно. Обновлено/добавлено записей: {result.totals["new"] + result.totals["updated"]}. Ошибок: {result.totals["errors"]}.'))

        else:
            queryset = ModelClass.objects.all()
            dataset = resource_class.export(queryset)
            serialized_data = selected_format.export_data(dataset)

            with open(file_path, 'wb') as f:
                f.write(serialized_data.read())

            self.stdout.write(self.style.SUCCESS(f'Экспорт завершен успешно. Количество записей: {queryset.count()}'))