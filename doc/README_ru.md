# Проект чат-бота с плагинами и настройкой приложения через Dynaconf

В настоящее время поддерживаются плагины:
- Собеседник Гига Чат
- Мониторинг серверов IRIS
- Репортер по проблеме из GitLab
- Прогноз погоды /weather_list - список /weather_Moscow в Москве на день и 7 дней 
  на основе погодного сервиса https://open-meteo.com/en/docs#location_and_time 
  и сервис обратного геокодирования https://nominatim.openstreetmap.org/reverse
- Сервис получения статей из Википедии. Например, /wiki_Snow или <code>/wiki_Снег</code> или <code>wiki_Снеговик</code>
- Сервис агрегации rss новостей. /news_list - список лент

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

Создайте файл `.env` скопируйте и вставьте это или просто запустите `cp env_example .env`
Создайте файл `dynaconf.yaml` скопируйте и вставьте это или просто запустите `cp dynaconf.example.yaml dynaconf.yaml`, не забудьте изменить токены:
В файле .env нужно определить переменную ENV_FOR_DYNACONF=dev значение которой ссылается на раздел параметров в файле dynaconf.yaml

Запустите миграции для настройки базы данных SQLite:
``` bash
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

Экспортировать модели
``` bash
python manage.py dumpdata myapp.Location --output=location_data.json
```
Загручить данные
``` bash
python manage.py loaddata location_data.json
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

# Благодарности автору

https://github.com/ohld/django-telegram-bot

### Проверьте пример бота, который использует код из основной ветки: [t.me/djangotelegrambot](https://t.me/djangotelegrambot)
## Особенности

* База данных: Postgres, Sqlite3, MySQL — решать вам!
* Панель администратора (спасибо [Django](https://docs.djangoproject.com/en/3.1/intro/tutorial01/))
* Фоновые задания с использованием [Celery](https://docs.celeryproject.org/en/stable/)
* [Готовое к производству](https://github.com/ohld/django-telegram-bot/wiki/Production-Deployment-using-Dokku) развертывание с использованием [Dokku](https://dokku.com)
* Использование API Telegram в режиме опроса или [webhook](https://core.telegram.org/bots/api#setwebhook)
* Экспорт всех пользователей в `.csv`
* Собственные команды Telegram в menu](https://github.com/ohld/django-telegram-bot/blob/main/.github/imgs/bot_commands_example.jpg)
* Чтобы редактировать или удалять эти команды, вам нужно будет использовать метод бота `set_my_commands`, как в [tgbot.dispatcher.setup_my_commands](https://github.com/ohld/django-telegram-bot/blob/main/tgbot/dispatcher.py#L150-L156)

Встроенные методы бота Telegram:
* `/broadcast` — отправить сообщение всем пользователям (команда администратора)
* `/export_users` — бот отправляет вам информацию о ваших пользователях в файле .csv (команда администратора)
* `/stats` — показать базовую статистику бота
* `/ask_for_location` — записать местоположение пользователя при получении и выполнить обратное геокодирование, чтобы получить страну, город и т. д.

## Содержание

* [Как запустить локально](https://github.com/ohld/django-telegram-bot/#how-to-run)
* [Быстрый старт с опросом и SQLite](https://github.com/ohld/django-telegram-bot/#quickstart-polling--sqlite)
* [Использование docker-compose](https://github.com/ohld/django-telegram-bot/#run-locally-using-docker-compose)
* [Развертывание в производство](https://github.com/ohld/django-telegram-bot/#deploy-to-production)
* [Использование докку](https://github.com/ohld/django-telegram-bot/#deploy-using-dokku-step-by-step) 
* [Вебхук Telegram](https://github.com/ohld/django-telegram-bot/#https--telegram-bot-webhook)