import os
import sys
import django
import csv
import datetime
from django.core.exceptions import ObjectDoesNotExist

# Определение базовой директории проекта
BASE_DIR = os.path.dirname( os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR)
sys.path.append(BASE_DIR)  # Добавляем путь к проекту в sys.path

# Установка переменной окружения для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'dtb.settings')

# Инициализация Django
try:
    django.setup()
except Exception as e:
    print(f"Ошибка инициализации Django: {e}")
    sys.exit(1)
from django.contrib.auth.models import User

def export_users_to_csv(filename='users.csv'):
    """
    Экспортирует всех пользователей в CSV-файл.
    """
    fields = [f.name for f in User._meta.fields]
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        for user in User.objects.all():
            row = {}
            for field in fields:
                value = getattr(user, field)
                # Преобразование дат в строковый формат
                if isinstance(value, datetime.datetime):
                    value = value.isoformat()
                # Обработка пустых значений
                elif value is None:
                    value = ''
                row[field] = value
            writer.writerow(row)
    print(f'Экспортировано {User.objects.count()} пользователей в {filename}')

def import_users_from_csv(filename='users.csv'):
    """
    Импортирует пользователей из CSV-файла в базу данных.
    Обновляет существующие записи по полю `id` или создает новые.
    """
    converters = {
        'id': int,
        'last_login': lambda x: datetime.datetime.fromisoformat(x) if x else None,
        'is_superuser': lambda x: x.lower() == 'true',
        'is_staff': lambda x: x.lower() == 'true',
        'is_active': lambda x: x.lower() == 'true',
        'date_joined': lambda x: datetime.datetime.fromisoformat(x)
    }
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Преобразование значений согласно типам данных
            data = {}
            for key, value in row.items():
                if key in converters:
                    data[key] = converters[key](value)
                else:
                    data[key] = value
            
            # Поиск пользователя по ID
            user_id = data.get('id')
            if user_id is not None:
                try:
                    user = User.objects.get(id=user_id)
                    # Обновление полей (кроме id)
                    for field, val in data.items():
                        if field != 'id':
                            setattr(user, field, val)
                    user.save()
                except ObjectDoesNotExist:
                    User.objects.create(**data)
            else:
                User.objects.create(**data)
    
    print(f'Импортировано {len(list(reader))} пользователей из {filename}')

if __name__ == '__main__':
    # Экспорт данных
    #export_users_to_csv('test/sysusers.csv')
    
    # Импорт данных (раскомментируйте для использования)
    import_users_from_csv('test/sysusers.csv')