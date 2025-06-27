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
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
import feedparser, random
from datetime import datetime

# Добавить проверку на роль ''
plugin_news = get_plugins('').get('NEWS')

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = "/news_list - получить список лент СМИ /news_100 /news_200 /news_300"
    text += '\n\r🔸/help '
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id,
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
        text = f'<b>Новости по контексту "{search_string}" из {len(sorted_news)} {title}</b>'
    else:
        text = f'<b>Новости: случайно выбрано {count} из {len(sorted_news)} {title}</b>'
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
    msg = text[:4081]+"...\n\n🔸/help /news_list /news_25"
    context.bot.send_message( 
        chat_id=upms.chat.id, text=msg, 
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML )



@check_groupe_user
def commands(update: Update, context: CallbackContext) -> None:
    upms = get_tele_command(update)
    telecmd = upms.text
    count = 10
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
        text = f"\n🔸/help /news_all или /news_0 - все новости, /news_10 - 10 новостей, <code>/news_Иран</code> - поиск по контексту 'Иран'"
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
            text=text+'\n🔸/help /news', parse_mode=ParseMode.HTML )
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
    write_news(rss_dict ,count ,context ,upms, "", search_string)
