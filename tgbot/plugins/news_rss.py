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

# Список ссылок на RSS-каналы
rss_urls = [
    'https://rg.ru/xml/index.xml',
    'https://www.pnp.ru/rss/index.xml'
]

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

@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    count = 10
    _co = telecmd.split('news')[1]
    if _co=='list':
        pass
    if _co:
        count=int(_co)

    text = f'<b>Последние новости {count}</b>'
    
    unique_titles = set()  # Для отслеживания уникальных заголовков
    sorted_news = []       # Итоговый список новостей

    for url in rss_urls:
        news_items = fetch_news(url)
        for item in news_items:
            if item['title'] not in unique_titles:
                unique_titles.add(item['title'])
                sorted_news.append(item)

    # Сортируем новости по дате и времени публикации (убывание)
    sorted_news.sort(key=lambda x: x['published'], reverse=True)

    for news_item in sorted_news[:count]:  # выводим первые 10 новостей
        text +=f"\n👉{news_item['title']} 🎯{news_item['source']} 📆({news_item['published']})"
        text +=f"\n\t 🔍{news_item['link']}"  # выводить ссылку отдельно
    
    context.bot.send_message(
        chat_id=u.user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )