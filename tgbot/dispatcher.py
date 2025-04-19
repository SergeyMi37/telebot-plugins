"""
    Telegram event handlers
"""
from telegram.ext import (
    Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
)

from dtb.settings import DEBUG
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST
from tgbot.handlers.broadcast_message.static_text import broadcast_command,reports_command
from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON

from tgbot.handlers.utils import files, error
from tgbot.handlers.admin import handlers as admin_handlers
from tgbot.handlers.admin import reports_gitlab, servers_iris
from tgbot.handlers.location import handlers as location_handlers
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.main import bot
from tgbot.handlers.admin.giga_chat import ask_giga
from tgbot.handlers.admin.reports_gitlab import PROJ_EN
from tgbot.handlers.admin.servers_iris import plugins_iris

def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    # onboarding
    dp.add_handler(CommandHandler("start", onboarding_handlers.command_start))
    dp.add_handler(CommandHandler("help", onboarding_handlers.command_help)) 
    dp.add_handler(CommandHandler("plugins", onboarding_handlers.command_plugins)) 
 
    # Если есть доступ к плагину IRIS
    if plugins_iris:
        dp.add_handler(CommandHandler("servers", servers_iris.command_servers)) 
        # Сервера ИРИС
        dp.add_handler(
            MessageHandler(Filters.regex(rf'^/s(/s)?.*'), broadcast_handlers.server)
        )
   
    # Если есть доступ к плагину GITLAB
    if PROJ_EN:
        dp.add_handler(CommandHandler("daily", reports_gitlab.command_daily)) 
        dp.add_handler(CommandHandler("yesterday", reports_gitlab.command_yesterday)) 
        for _en in PROJ_EN.split(','):
            dp.add_handler(CommandHandler(f"daily_{_en}_noname", reports_gitlab.command_daily_rating_noname)) 
            dp.add_handler(CommandHandler(f"daily_{_en}", reports_gitlab.command_daily_rating)) 
            dp.add_handler(CommandHandler(f"yesterday_{_en}", reports_gitlab.command_daily_rating)) 
            dp.add_handler(CommandHandler(f"weekly_{_en}", reports_gitlab.command_weekly_rating)) 

    # admin commands
    dp.add_handler(CommandHandler("admin", admin_handlers.admin))
    dp.add_handler(CommandHandler("stats", admin_handlers.stats))
    dp.add_handler(CommandHandler('export_users', admin_handlers.export_users))

    # location
    dp.add_handler(CommandHandler("ask_location", location_handlers.ask_for_location))
    dp.add_handler(MessageHandler(Filters.location, location_handlers.location_handler))

    # secret level
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.secret_level, pattern=f"^{SECRET_LEVEL_BUTTON}"))
    
    # reports
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{reports_command}(/s)?.*'), broadcast_handlers.reports)
    )
    
    # broadcast message
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{broadcast_command}(/s)?.*'), broadcast_handlers.broadcast_command_with_message)
    )
    dp.add_handler(
        CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    )

    # files
    dp.add_handler(MessageHandler(
        Filters.animation, files.show_file_id,
    ))

    #dp.add_handler(MessageHandler(        Filters.document.txt, files.save_file_id,    ))
    dp.add_handler(MessageHandler(
        Filters.document, files.save_file_id,
    ))

    # Обработка всех текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    # EXAMPLES FOR HANDLERS
    # dp.add_handler(MessageHandler(Filters.text, <function_handler>))
    # dp.add_handler(MessageHandler(
    #     Filters.document, <function_handler>,
    # ))
    # dp.add_handler(CallbackQueryHandler(<function_handler>, pattern="^r\d+_\d+"))
    # dp.add_handler(MessageHandler(
    #     Filters.chat(chat_id=int(TELEGRAM_FILESTORAGE_ID)),
    #     # & Filters.forwarded & (Filters.photo | Filters.video | Filters.animation),
    #     <function_handler>,
    # ))

    return dp

# Функция-обработчик для текстовых сообщений
def handle_text_message(update, context):
    user = update.effective_user
    text = update.message.text
    # Логика обработки сообщения
    resp = ask_giga(text)
    # Ответ пользователю
    #print(f"User {user.first_name} На вопрос: {text}\n Получил ответ:{resp}")
    update.message.reply_text(f"Ответ Гиги: '{resp}'")

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
