<img src="https://github.com/SergeyMi37/telebot-plugins/raw/main/doc/logo_min.png">

## telebot-plugins.

Chatbot project with Django Admin and plugins

[Документация](https://github.com/SergeyMi37/telebot-plugins/raw/main/doc/README_ru.md)

[Групп разработки бота](https://t.me/+LXQkVtnHqSM1ZmZi) 

[Групп техподдержки бота](https://t.me/+__Qezxf7-E0xY2I6)

[Демо бота](https://t.me/jff_sss_bot)

# What's new

Modules are implemented in plug-ins:
- /data - Getting information on phones and Organizations (You need a user key https://dadata.ru/api /)
- /chinese - For those who learn Chinese. Search for the etymology of hieroglyphs and translate into English (Using the playwrite library and website https://www.archchinese.com / )

# Chatbot project with Django admin panel and with plug-ins and application configuration via Dynaconf

Currently, plugins are supported:
- /chat - An interlocutor with a Gigachat model (you need a developer key)
- /chat_list - Chats with models from Ollama (you need the Ollama platform installed on the local network)
- /iris - Monitoring of IRIS servers from Intersystems 
- /gitlab - Task reporter from GitLab projects (you need a token to read from the project)
- /weather - Weather forecast /weather_list - list /weather_Moscow in Moscow for a day and 7 days 
  based on the weather service https://open-meteo.com/en/docs#location_and_time 
  and the reverse geocoding service https://nominatim.openstreetmap.org/reverse
- /wiki - A service for getting articles from Wikipedia. For example, /wiki_Snow or /wiki_ - enter the word
- /news is an rss news aggregation service. /news_list - list of feeds
- /inet - Internet search service /inet_ddg_ - currently only in the DuckDuckGo search engine
- /admin - Group administration module
    deleting system information about entering and exiting groups
    removing a user from a group for writing prohibited words
receiving reports on users and changes in the CSV
- /code - Module format for obtaining information from regional code directories of the Russian Federation and searching for a country at the beginning of the code

# Install locally

<p align="left">
    <img src="https://github.com/SergeyMi37/telebot-plugins/raw/main/doc/Screenshot_1.png">
</p>

``` bash
git clone https://github.com/SergeyMi37/telebot-plugins
cd telebot-plugins
```

Create virtual environment (optional)
``` bash
python3 -m venv env-lin
source env-lin/bin/activate

# Create virtual environment for Windows
python -m venv env-win
source env-win/Scripts/activate

# Install all requirements:
pip install -r requirements.txt
```

Create `.env` file copy-paste this or just run `cp doc/env_example .env` 
Create `dynaconf.yaml` file copy-paste this or just run `cp doc/dynaconf.example.yaml dynaconf.yaml`, don't forget to change tokens:


Run migrations to setup SQLite database:
``` bash
python manage.py makemigrations
python manage.py migrate
```

Create superuser to get access to admin panel:
``` bash
python manage.py createsuperuser
```
or 
``` bash 
# .env DJANGO_SUPERUSER_PASSWORD=demo
python manage.py createsuperuser --noinput --username adm --email adm@localhost.com 
```


Run bot in polling mode:
``` bash
python run_polling.py 
```

If you want to open Django admin panel which will be located on http://localhost:8000/tgadmin/:
``` bash
python manage.py runserver
```

## Утилиты командной строки

```
#  Статистика всех моделей Django:
python manage.py model_stats

#  Детальная информация о конкретной модели:
python manage.py check_model users.updates

#  Экспорт модели в файл json:
python manage.py model_import --model django_celery_beat.PeriodicTasks --file test.json --format json --import 0
# или
python manage.py model_import --model django_celery_beat.PeriodicTasks --file test.json --format json

#  Экспорт модели в файл csv (по умолчанию):
python manage.py model_import --model django_celery_beat.PeriodicTasks --file sysotiom.csv --format csv

#  Импорт модели из файла json в режиме --dry-run - сухой запуск, без реального импорта:
python manage.py model_import --model users.User --file users.json --format json --import 1 --dry-run

#  Импорт модели из файла json:
python manage.py model_import --model users.User --file users.json --format json --import 1
```

## Run locally using docker-compose
If you want just to run all the things locally, you can use Docker-compose which will start all containers for you.


### Docker-compose

To run all services (Django, Postgres, Redis, Celery) at once:
``` bash
docker-compose up -d --build
```

Check status of the containers.
``` bash
docker ps -a
```
### To see all names of the container:

``` bash
 docker-compose ps --services
```

### Enter django shell:

``` bash
docker exec -it dtb_bot bash
```

### Create superuser for Django admin panel

``` bash 
python manage.py createsuperuser
```
or 
``` bash 
python manage.py createsuperuser --noinput --username adm --email adm@localhost.com # .env DJANGO_SUPERUSER_PASSWORD=demo
```

### To see logs of the container:

``` bash
docker logs -f
```
### To see logs of the container bot:

``` bash
 docker logs -f bot
```
