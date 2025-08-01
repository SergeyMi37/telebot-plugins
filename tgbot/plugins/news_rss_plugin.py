# Plugin Новости из ленты rss ----- стандарный
# Name Plugin: NEWS
    # - NEWS:
    #     - blocked = 1
    #     - desc = Сервис агрегации новостей 
# имя плагина NEWS должно совпадать с именем в конфигурации Dynaconf
# имя плагина news должно быть первым полем от _ в имени файла news_rss_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class NewsRSSPlugin(BasePlugin):
#    def setup_handlers(self, dp):

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext
from dtb.settings import get_plugins_for_roles
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
import feedparser, random

# Добавить проверку на роль ''
plugin_news = get_plugins_for_roles('').get('NEWS')

rss_dict = {}
if plugin_news:
    for key, val in plugin_news.items():
        if key[0:4]=='rss_':
            rss_dict.setdefault(key,val)

CODE_INPUT = range(1)
_news_help = "\n/news_list - получить список лент СМИ " \
    "\n/news_all или /news_0 - все новости, \n/news_10 - 10 новостей, \n/news_30 - 30 новостей, \n/news_ Ввести контекст поиска в загловков"

# plugins/news_rss_plugin.py
from tgbot.plugins.base_plugin import BasePlugin

def fetch_news(url):
    """Получение списка новостей из RSS-канала"""
    news_list = []
    feed = feedparser.parse(url)
    for entry in feed.entries:
        # Извлекаем важные поля каждой записи
        title = entry.get('title', '')
        link = entry.get('link', '')
        published = entry.get('published', '')  # Дата и время публикации
        
        if all([title, link]):
            news_list.append({
                'title': title,
                'link': link,
                'published': published,
                'source': feed.feed.title
            })
    return news_list

def write_news(rss_dict, count, context,upms, title="по всем лентам", search_string=None):
    unique_titles = set()  # Для отслеживания уникальных заголовков
    sorted_news = []       # Итоговый список новостей

    for key, val in rss_dict.items():
        news_items = fetch_news(val)
        for item in news_items:
            if item['title'] not in unique_titles:
                unique_titles.add(item['title'])
                # Проверяем наличие поискового запроса в заголовке
                if search_string is None:
                    sorted_news.append(item)
                elif search_string.lower() in item['title'].lower():
                    sorted_news.append(item)

    # Сортируем новости по дате и времени публикации (убывание)
    #sorted_news.sort(key=lambda x: x['published'], reverse=True)
    
    if count>len(sorted_news):
        count = len(sorted_news)
    selected_news = random.sample(sorted_news, min(count, len(sorted_news)))

    if search_string:
        text = f'<b>Новости по контексту "{search_string}" из {len(unique_titles)} {title}</b>'
    else:
        text = f'<b>Новости: случайно выбрано {count} из {len(unique_titles)} {title}</b>'
    num=0
    for news_item in selected_news[:count]:  # выводим первые 10 новостей
        #text +=f"\n👉{news_item['title']} 🎯{news_item['source']} 📆({news_item['published']})"
        num += 1
        #it = f"\n{num}.🔍<a href=\"{news_item['link']}\">{news_item['title']} 📆({news_item['published'][:16]})</a>"
        it = f"\n{num}.🔷<a href=\"{news_item['link']}\">{news_item['title']}</a> {news_item['source'][:16]}..."
        if len(text+it)>4081:
            context.bot.send_message(
                chat_id=upms.chat.id,
                text = text+"\n🔸/help\n", 
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML)
            text=it
        else:
            text += f"{it}"
    msg = text[:4081]+"...\n\n🔸/help /news_list /news_ "
    context.bot.send_message( 
        chat_id=upms.chat.id, text=msg, 
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML )

def request_news(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите контекс поиска в новостных заголовках /cancel - отмена")
    return CODE_INPUT

def check_news(update: Update, context):
    upms = get_tele_command(update)
    upms.reply_text(".🕒.минутку...")
    cntx = upms.text
    write_news(rss_dict ,111111111 ,context ,upms, "", cntx)
    # context.bot.send_message(
    #     chat_id=upms.chat.id,
    #     text=response + '\n\r🔸/help /code',
    #     disable_web_page_preview=True,
    #     parse_mode=ParseMode.HTML
    # )
    return ConversationHandler.END

def cancel_news(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("Отмена")
    return ConversationHandler.END


class NewsRSSPlugin(BasePlugin):
    def setup_handlers(self, dp):

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('news_', request_news)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_news),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_news),
            ]
        )
        dp.add_handler(conv_handler)
        dp.add_handler(MessageHandler(Filters.regex(rf'^/news(/s)?.*'), self.commands))
        dp.add_handler(CallbackQueryHandler(self.button, pattern="^button_news"))

    def commands(self, update, context):
        commands_(update, context)
    
    def button(self, update, context):
        button_(update, context)

@check_groupe_user
def button_(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = _news_help
    text += '\n\r🔸/help /news_'
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


@check_groupe_user
def commands_(update: Update, context: CallbackContext) -> None:
    upms = get_tele_command(update)
    telecmd = upms.text
    count = 10
    if not plugin_news:
        upms.reply_text("🕒.минутку...")
        return
    # Список всех ссылок на RSS-каналы
    rss_dict = {}
    for key, val in plugin_news.items():
        if key[0:4]=='rss_':
            rss_dict.setdefault(key,val)
    
    if '/news_' in telecmd:
        arg = telecmd.split('/news_')[1]
    else:
        arg = telecmd.split('/news')[1]
    
    search_string = ""
    if 'rss_' in arg:
        rd = {}
        key = 'rss_'+arg.split('rss_')[1]
        if plugin_news.get(key):
            rd.setdefault(key,plugin_news.get(key))
            write_news(rd,300,context,upms ,"по ленте "+key)
        return       
    elif len(arg) == 0:
        text = _news_help
        context.bot.send_message( 
            chat_id=upms.chat.id,
            text=text, parse_mode=ParseMode.HTML )
        return       
    elif arg=='list':
        text=""
        for key, val in rss_dict.items():
            text += f"\n🔍 /news_{key}"
        context.bot.send_message( 
            chat_id=upms.chat.id,
            text=text+'\n🔸/help /news_', parse_mode=ParseMode.HTML )
        return
    elif arg=="all" or arg=="0": # все новости
        count = 111111111111
    elif arg.isdigit(): # колчество новосте вывести в чат с ботом
        try:
            count=int(arg)
        except Exception as e:
            err = f'Введите число. {e.args.__repr__()}'
            context.bot.send_message(
                chat_id=upms.chat.id,
                text=err, parse_mode=ParseMode.HTML )
            return
    else: # поиск по контексту 
        search_string = arg
        count = 111111111111
    upms.reply_text("🕒.минутку...")
    write_news(rss_dict ,count ,context ,upms, "", search_string)
