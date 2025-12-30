# Name Plugin: chinese
    # - CHINESE:
    #     - desc = Сервис для скачивания роликов с Ютуба и ВкВидео и обмена ссылками между пользователями бота
# имя плагина MEDIA должно совпадать с именем в конфигурации Dynaconf
# имя плагина media должно быть первым полем от _ в имени файла chinese_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class MEFIAPlugin(BasePlugin):
#    def setup_handlers(self, dp):
if __name__ != "__main__":
    from telegram import ParseMode, Update
    from telegram.ext import CallbackContext
    # from dtb.settings import get_plugins_for_roles
    # from dtb.settings import logger
    from tgbot.handlers.utils.info import get_tele_command
    from tgbot.handlers.utils.decorators import check_groupe_user
    from users.models import User
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
    from tgbot.plugins.base_plugin import BasePlugin
    from tgbot.plugins.chinese_etymology import get_character_etymology
    # Добавить проверку на роль ''
    #plugin_wiki = get_plugins_for_roles('').get('WIKI')

    plugin_cmd = "chinese"
    CODE_INPUT = range(1)
    plugin_help = f'Учить китайские иероглифы. 🔸/help /{plugin_cmd} /{plugin_cmd}_ - введите 1 иероглиф для поиска этимолгии, или больше для перевода' 


    def request_p(update: Update, context):
        """Запрашиваем у пользователя """
        upms = get_tele_command(update)
        upms.reply_text(f"Введите иероглифы или /cancel_{plugin_cmd} - отмена")
        return CODE_INPUT

    def check_p(update: Update, context):
        upms = get_tele_command(update)
        _in = upms.text
        if not _in:
            _out = f'Нечего не введено {_in}\n\r🔸/help /{plugin_cmd}_' 
        elif len(_in)==1:
            upms.reply_text(".等一下...ждите")
            # вызов сервиса поиска этимологии иероглифа
            print('---')
            status, text = get_character_etymology(_in,verbose=False) # verbose=True - показать лог
            print('---',status,text)
            _out = f'Результат поиска этимологии {_in}\n\r🔸/help /{plugin_cmd}_ \n' 
            _out += text
        else:
            # вызов функции перевода с параметрами "с китайского на русский "
            _out = f'Результат перевода {_in}\n\r🔸/help /{plugin_cmd}_' 
        context.bot.send_message(
            chat_id=upms.chat.id,
            text=_out,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    def cancel_p(update: Update, context):
        """Завершаем диалог"""
        upms = get_tele_command(update)
        upms.reply_text("Разговор завершен.")
        return ConversationHandler.END

    class PPlugin(BasePlugin):
        def setup_handlers(self, dp):
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler(f'{plugin_cmd}_', request_p)],
                states={
                    CODE_INPUT: [
                        MessageHandler(Filters.text & (~Filters.command), check_p),
                    ],
                },
                fallbacks=[
                    CommandHandler(f'cancel_{plugin_cmd}', cancel_p),
                ]
            )
            dp.add_handler(conv_handler)
            dp.add_handler(MessageHandler(Filters.regex(rf'^/{plugin_cmd}(/s)?.*'), commands))
            dp.add_handler(CallbackQueryHandler(button, pattern=f"^button_{plugin_cmd}"))

    @check_groupe_user
    def button(update: Update, context: CallbackContext) -> None:
        #user_id = extract_user_data_from_update(update)['user_id']
        u = User.get_user(update, context)
        upms = get_tele_command(update)
        text = "Введите ..."
        text += plugin_help
        context.bot.edit_message_text(
            text=text,
            chat_id=upms.chat.id, #  u.user_id,
            message_id=update.callback_query.message.message_id,
            parse_mode=ParseMode.HTML
        )

    @check_groupe_user
    def commands(update: Update, context: CallbackContext) -> None:
        #u = User.get_user(update, context)
        upms = get_tele_command(update)
        telecmd = upms.text
        #if telecmd == '/':
        _out = plugin_help
        context.bot.send_message(
            chat_id=upms.chat.id,
            text=_out,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )

