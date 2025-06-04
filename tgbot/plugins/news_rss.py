# Plugin Новости из ленты rss
# Name Plugin: NEWS
    # - NEWS:
    #     - blocked = 1
    #     - desc = Сервис агрегации новостей 

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_blocked_user
from users.models import User
import feedparser
from datetime import datetime

# Добавить проверку на роль ''
plugin_news = get_plugins('').get('NEWS')

@check_blocked_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    u = User.get_user(update, context)
    text = "/news_list - получить список лент СМИ /news_100 /news_200 /news_300"
    text += '\n\r/help '
    context.bot.edit_message_text(
        text=text,
        chat_id=u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

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

def write_news(rss_dict,count,context,u,title="по всем лентам"):
    unique_titles = set()  # Для отслеживания уникальных заголовков
    sorted_news = []       # Итоговый список новостей

    for key, val in rss_dict.items():
        news_items = fetch_news(val)
        for item in news_items:
            if item['title'] not in unique_titles:
                unique_titles.add(item['title'])
                sorted_news.append(item)

    # Сортируем новости по дате и времени публикации (убывание)
    sorted_news.sort(key=lambda x: x['published'], reverse=True)
    if count>len(sorted_news):
        count = len(sorted_news)
    text = f'<b>Новости {count} из {len(sorted_news)} {title}</b>'
    num=0
    for news_item in sorted_news[:count]:  # выводим первые 10 новостей
        #text +=f"\n👉{news_item['title']} 🎯{news_item['source']} 📆({news_item['published']})"
        num += 1
        #it = f"\n{num}.🔍<a href=\"{news_item['link']}\">{news_item['title']} 📆({news_item['published'][:16]})</a>"
        it = f"\n{num}.🔷<a href=\"{news_item['link']}\">{news_item['title']}🔹({news_item['source']})</a>"
        if len(text+it)>4081:
            context.bot.send_message( chat_id=u.user_id, text=text, parse_mode=ParseMode.HTML)
            text=it
        else:
            text = text + it
    msg = text[:4081]+"...\n/help /news_list /news_25"
    context.bot.send_message( chat_id=u.user_id, text=msg, parse_mode=ParseMode.HTML )

@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    count = 10
    # Список всех ссылок на RSS-каналы
    rss_dict = {}
    for key, val in plugin_news.items():
        if key[0:4]=='rss_':
            rss_dict.setdefault(key,val)

    arg = telecmd.split('/news_')[1]
    if 'rss_' in arg:
        rd = {}
        key = 'rss_'+arg.split('rss_')[1]
        if plugin_news.get(key):
            rd.setdefault(key,plugin_news.get(key))
            write_news(rd,300,context,u,"по ленте "+key)
        return        
    elif arg=='list':
        text=""
        for key, val in rss_dict.items():
            text += f"\n/news_{key} 🔍{val}"
        context.bot.send_message( chat_id=u.user_id, text=text+'\n/help', parse_mode=ParseMode.HTML )
        return
    elif arg: # колчество новосте вывести в чат с ботом
        try:
            count=int(arg)
        except Exception as e:
            err = f'Введите число. {e.args.__repr__()}'
            context.bot.send_message( chat_id=u.user_id, text=err, parse_mode=ParseMode.HTML )
            return
    write_news(rss_dict,count,context,u)
