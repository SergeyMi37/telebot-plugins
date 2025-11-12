# management/commands/model_stats.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.db.models import Count

class Command(BaseCommand):
    help = 'Выводит статистику по моделям'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("📈 Статистика моделей Django"))
        
        all_models = apps.get_models()
        
        for model in all_models:
            try:
                count = model.objects.count()
                
                # Собираем информацию о полях
                fields = model._meta.get_fields()
                field_types = {}
                
                for field in fields:
                    field_type = type(field).__name__
                    field_types[field_type] = field_types.get(field_type, 0) + 1
                # print("---",model.__name__,model.__module__)
                # print("---",dir(model))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n📊 {model._meta.app_label}.{model.__name__}:"
                    )
                )
                self.stdout.write(f"   📝 Записей в БД: {count}")
                self.stdout.write(f"   🗂️  Всего полей: {len(fields)}")
                
                for field_type, type_count in field_types.items():
                    self.stdout.write(f"      • {field_type}: {type_count}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ Ошибка для {model._meta.app_label}.{model._meta.model_name}: {e}"
                    )
                )