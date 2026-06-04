import json
import logging
from django.views import View
from django.http import JsonResponse
from telegram import Update
from django.views.decorators.csrf import csrf_exempt
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

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        try:
            # Парсим JSON из запроса
            json_data = json.loads(request.body)
            
            # Логируем для отладки
            logger.info(f"Webhook received. Update ID: {json_data.get('update_id', 'unknown')}")
            
            # Преобразуем JSON в объект Update
            update = Update.de_json(json_data, bot)
            
            # Обрабатываем через dispatcher (здесь регистрируются все команды)
            dispatcher.process_update(update)
            
            # Если нужно асинхронное выполнение через Celery, раскомментируйте:
            # if not settings.DEBUG:
            #     from tgbot.tasks import process_telegram_event
            #     process_telegram_event.delay(json_data)
            # else:
            #     update = Update.de_json(json_data, bot)
            #     dispatcher.process_update(update)
            
            return JsonResponse({"ok": True})
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return JsonResponse({"ok": False, "error": str(e)})

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