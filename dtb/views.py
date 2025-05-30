import json
import logging
from django.views import View
from django.http import JsonResponse
from telegram import Update

from dtb.celery import app
from dtb.settings import DEBUG
from tgbot.dispatcher import dispatcher
from tgbot.main import bot
from tgbot.plugins import servers_iris

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def index(request):
    return JsonResponse({"hello": "load .../tgadmin/"})


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        if DEBUG:
            process_telegram_event(json.loads(request.body))
        else:
            # Process Telegram event in Celery worker (async)
            # Don't forget to run it and & Redis (message broker for Celery)!
            # Locally, You can run all of these services via docker-compose.yml
            process_telegram_event.delay(json.loads(request.body))

        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):  # for debug 
        return JsonResponse({"ok": "Get request received! But nothing done"})

# Если есть доступ к плагину IRIS
@app.task(ignore_result=True)
def process_custom_telegram_event(update_json):
    print('--=-= update_json =',update_json) # ТО что пришло из такска из параметра Arguments
    if update_json["message"]["condition"]:
        cond = update_json["message"]["condition"]
        res = servers_iris.command_server(cond)
        print('--== res , cond=',res, cond)
        if '<b>Err</b>' in res:
            update_json["message"]["text"] = "/s_PROD_SYS_AlertsView_На_серверах_есть_проблеммы "
        else:
            print('--== Команда не послана в телегу')
            return
           
    update = Update.de_json(update_json, bot)
    print('--== Команда послана в телегу',update)
    dispatcher.process_update(update)