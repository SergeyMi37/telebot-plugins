# management/commands/check_model.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models

class Command(BaseCommand):
    help = 'Детальная информация о конкретной модели'

    def add_arguments(self, parser):
        parser.add_argument('model_path', type=str, help='Путь к модели в формате app_label.ModelName')

    def handle(self, *args, **options):
        model_path = options['model_path']
        
        try:
            if '.' in model_path:
                app_label, model_name = model_path.split('.')
                model = apps.get_model(app_label, model_name)
            else:
                # Ищем модель по всем приложениям
                model = None
                for app_model in apps.get_models():
                    if app_model._meta.model_name == model_path:
                        model = app_model
                        break
                
                if not model:
                    raise LookupError(f"Модель {model_path} не найдена")
            
            self.print_detailed_model_info(model)
            
        except LookupError as e:
            self.stdout.write(self.style.ERROR(f"❌ {e}"))

    def print_detailed_model_info(self, model):
        """Выводит детальную информацию о модели"""
        meta = model._meta
        
        self.stdout.write(self.style.SUCCESS(f"\n🔍 Детальная информация о модели:"))
        self.stdout.write(f"   🏷️  Приложение: {meta.app_label}")
        self.stdout.write(f"   📝 Модель: {meta.model_name}")
        self.stdout.write(f"   📖 Отображаемое имя: {meta.verbose_name}")
        self.stdout.write(f"   📖 Множественное имя: {meta.verbose_name_plural}")
        self.stdout.write(f"   🗃️  Таблица БД: {meta.db_table}")
        self.stdout.write(f"   🔗 Абстрактная: {meta.abstract}")
        self.stdout.write(f"   👥 Managed: {meta.managed}")
        self.stdout.write(f"   📍 Ordering: {meta.ordering}")
        
        self.stdout.write(f"\n   🗂️  Поля ({len(meta.fields)}):")
        for field in meta.fields:
            self.print_field_details(field)
        
        # Связи
        relations = [f for f in meta.get_fields() if f.auto_created and not f.concrete]
        if relations:
            self.stdout.write(f"\n   🔗 Связи ({len(relations)}):")
            for relation in relations:
                self.stdout.write(f"      • {relation.name} ({type(relation).__name__})")

    def print_field_details(self, field):
        """Выводит детали поля"""
        field_info = f"      • {field.name} ({type(field).__name__})"
        
        if hasattr(field, 'max_length') and field.max_length:
            field_info += f" max_length={field.max_length}"
        
        if field.primary_key:
            field_info += " PRIMARY KEY"
        if field.unique:
            field_info += " UNIQUE"
        if field.null:
            field_info += " NULL"
        if field.blank:
            field_info += " BLANK"
        if field.default != models.NOT_PROVIDED:
            field_info += f" default={field.default}"
        
        if field.choices:
            field_info += f" choices({len(field.choices)})"
        
        if field.help_text:
            field_info += f" - {field.help_text}"
        
        self.stdout.write(field_info)