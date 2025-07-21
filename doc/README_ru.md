# Проект чат-бота с плагинами и настройкой приложения через Dynaconf

В настоящее время поддерживаются плагины:
- Собеседник Гига Чат
- Мониторинг серверов IRIS
- Репортер по проблеме из GitLab
- Прогноз погоды /weather_list - список /weather_Moscow в Москве на день и 7 дней 
  на основе погодного сервиса https://open-meteo.com/en/docs#location_and_time 
  и сервис обратного геокодирования https://nominatim.openstreetmap.org/reverse
- Сервис получения статей из Википедии. Например, /wiki_Snow или /wiki_ - ввести слово
- Сервис агрегации rss новостей. /news_list - список лент
- Сервис поиска в интернет /inet /inet_ddg_ - пока только в поисковой системе DuckDuckGo
- Модуль администрирования в группах
    удаление системной информации о входе и выходе из групп, изменения фото 
    удаления пользователя из группы за написание запрещенных слов
- Модуль получения информации из справочников кодов регионов РФ и поиск страны по началу штихкода

``` bash
git clone https://github.com/SergeyMi37/telebot-plugins
cd django-telegram-bot
```

Создать виртуальную среду (необязательно)
``` bash
python3 -m venv env
source env/bin/activate
```

Создать виртуальную среду для Windows
``` bash
python -m venv env
source env/Scripts/activate
```

Установите все требования:
```
pip install -r requirements.txt
```

Создайте файл `.env` скопируйте и вставьте это или просто запустите `cp doc/env_example .env`
Создайте файл `dynaconf.yaml` скопируйте и вставьте это или просто запустите `cp doc/dynaconf.example.yaml dynaconf.yaml`, не забудьте изменить токены:
В файле .env нужно определить переменную ENV_FOR_DYNACONF=dev значение которой ссылается на раздел параметров в файле dynaconf.yaml
Иногда нужно выполнить `export ENV_FOR_DYNACONF=dev`

Запустите миграции для настройки базы данных:
``` bash
python manage.py makemigrations
python manage.py migrate
```

Создайте суперпользователя для доступа к панели администратора интервктивно:
``` bash
python manage.py createsuperuser
```
или автоматизировано:
``` bash
python manage.py createsuperuser --noinput --username adm --email adm@localhost.com # .env DJANGO_SUPERUSER_PASSWORD=demo
```

Запустите бота в режиме опроса:
``` bash
python run_polling.py
```

Если вы хотите открыть панель администратора Django, которая будет расположена по адресу http://localhost:8000/tgadmin/:
``` bash
python manage.py runserver
```
## Другие сервисные команды проекта

Экспортировать модели Location и User в файлы
``` bash
python manage.py dumpdata users.Location --indent=2 --output=downloads/location_data.json
python manage.py dumpdata users.User --indent=2 --output=downloads/users_data.json
```
Экспортировать все модели в файл за исключением системных Django
``` bash
python manage.py dumpdata --exclude auth.permission --exclude auth.user --exclude contenttypes --exclude auth.group --exclude admin.logentry --exclude sessions.session --indent 2 > db-init-telebot.json
```
Загрузить данные из файла
``` bash
python manage.py loaddata location_data.json
```

Выгрузить данные объектов в файл
``` bash
python manage.py export_group_roles doс/output.json
python manage.py import_group_roles --file doc/group_roles.json
```

Загрузить данные объектов из файла
``` bash
python manage.py import_options --file doc/options.json
python manage.py import_group_roles --file doc/group_roles.json
```

Запустить проверку проекта
``` bash
python manage.py check
```

## Запустите локально с помощью docker-compose
Если вы хотите просто запустить все локально, вы можете использовать Docker-compose, который запустит все контейнеры для вас.

### Docker-compose

Чтобы запустить все службы (Django, Postgres, Redis, Celery) одновременно:
``` bash
docker-compose up -d --build
```

Проверьте статус контейнеров.
``` bash
docker ps -a
```
Это должно выглядеть примерно так:
<p align="left">
<img src="https://github.com/ohld/django-telegram-bot/raw/main/.github/imgs/containers_status.png">
</p>

Попробуйте посетить <a href="http://0.0.0.0:8000/tgadmin">панель администратора Django</a>.

### Войдите в оболочку django:

``` bash
docker exec -it dtb_django bash
```

### Создайте суперпользователя для панели администратора Django

``` bash
python manage.py createsuperuser
```
или
``` bash
python manage.py createsuperuser --noinput --username adm --email adm@localhost.com # .env DJANGO_SUPERUSER_PASSWORD=demo
```

### Экспортировать модели Location и User в файлы
``` bash
docker exec -it dtb_django bash
...123:/code# python manage.py dumpdata users.Location --indent=2 --output=downloads/location_data.json
...123:/code# python manage.py dumpdata users.User --indent=2 --output=downloads/users_data.json
```

### Экспортировать\импортировать данные регулярных задач специальными командами 
``` bash
docker exec -it dtb_django bash
...123:/code# python manage.py export_celery_tasks --output downloads/my_tasks.json
...123:/code# python manage.py import_celery_tasks downloads/my_tasks.json --dry-run
```


### Чтобы просмотреть логи контейнера:

``` bash
docker logs -f
```
### Чтобы просмотреть все имена контейнера:

``` bash
docker-compose ps --services
```
### Чтобы просмотреть логи контейнерного бота:

``` bash
docker logs -f bot
```
