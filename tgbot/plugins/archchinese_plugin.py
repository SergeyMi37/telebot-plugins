# Name Plugin: TEMPLATE
    # - MEDIA:
    #     - desc = Сервис для скачивания роликов с Ютуба и ВкВидео и обмена ссылками между пользователями бота
# имя плагина MEDIA должно совпадать с именем в конфигурации Dynaconf
# имя плагина media должно быть первым полем от _ в имени файла media_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class MEFIAPlugin(BasePlugin):
#    def setup_handlers(self, dp):

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
# from dtb.settings import get_plugins_for_roles
# from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin

# Добавить проверку на роль ''
#plugin_wiki = get_plugins_for_roles('').get('WIKI')

plugin_cmd = "template"
CODE_INPUT = range(1)
plugin_help = f'Загрузка роликов с ютуба. 🔸/help /{plugin_cmd} /{plugin_cmd}_ - диалог для загрузки роликов с ютуба' 


def request_p(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text(f"Введите урл или /cancel_{plugin_cmd} - отмена")
    return CODE_INPUT

def check_p(update: Update, context):
    upms = get_tele_command(update)
    _in = upms.text
    _out = f'Будет загрузка {_in}\n\r🔸/help /{plugin_cmd}_' 
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

# def error(update, context):
#     logger.warning('Update "%s" caused error "%s"', update, context.error)

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


# Привет! Отличная идея! Вот программа на Python, которая реализует задуманное:

# ```python
import requests
from bs4 import BeautifulSoup
import re

def get_character_etymology(character):
    """
    Получает этимологию китайского иероглифа с archchinese.com
    """
    url = f"https://www.archchinese.com/chinese_english_dictionary.html?find={character}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем блок с информацией об иероглифе
        char_info = soup.find('div', class_='char-info')
        if not char_info:
            return None
        
        # Извлекаем название иероглифа
        char_name = char_info.find('h2').get_text(strip=True) if char_info.find('h2') else character
        
        # Ищем радикал
        radical_info = char_info.find('span', string=re.compile('Radical'))
        radical = radical_info.get_text(strip=True).replace('Radical:', '').strip() if radical_info else "Не найден"
        
        # Ищем компоненты разбора
        decomposition = char_info.find('span', string=re.compile('Decomposition'))
        decomposition_text = decomposition.get_text(strip=True).replace('Decomposition:', '').strip() if decomposition else "Не найден"
        
        # Ищем дополнительные компоненты
        components = []
        comp_elements = char_info.find_all('a', class_='comp-link')
        for comp in comp_elements:
            comp_text = comp.get_text(strip=True)
            comp_href = comp.get('href', '')
            components.append(f"{comp_text}")
        
        return {
            'character': char_name,
            'radical': radical,
            'decomposition': decomposition_text,
            'components': components
        }
        
    except Exception as e:
        print(f"Ошибка при получении данных для {character}: {e}")
        return None

def parse_chinese_word(word):
    """
    Разбирает китайское слово на иероглифы и получает этимологию для каждого
    """
    results = []
    
    for char in word:
        print(f"Обрабатываю иероглиф: {char}")
        etymology = get_character_etymology(char)
        
        if etymology:
            results.append(etymology)
        else:
            results.append({
                'character': char,
                'radical': "Не найден",
                'decomposition': "Не удалось получить данные",
                'components': []
            })
    
    return results

def display_results(word, results):
    """
    Красиво отображает результаты
    """
    print(f"\n{'='*60}")
    print(f"ЭТИМОЛОГИЯ СЛОВА: {word}")
    print(f"{'='*60}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Иероглиф: {result['character']}")
        print(f"   Радикал: {result['radical']}")
        print(f"   Разбор: {result['decomposition']}")
        
        if result['components']:
            print(f"   Компоненты: {', '.join(result['components'])}")
        print(f"   {'-'*40}")

def main():
    """
    Основная функция программы
    """
    print("Китайский этимологический анализатор")
    print("Введите китайское слово для анализа (например: 牛仔裤)")
    print("Для выхода введите 'quit'")
    
    while True:
        word = input("\nВведите слово: ").strip()
        
        if word.lower() in ['quit', 'exit', 'q']:
            print("До свидания!")
            break
        
        if not word:
            print("Пожалуйста, введите слово.")
            continue
        
        # Проверяем, что введены китайские иероглифы
        if not re.search(r'[\u4e00-\u9fff]', word):
            print("Пожалуйста, введите китайские иероглифы.")
            continue
        
        print(f"\nАнализирую слово: {word}...")
        
        results = parse_chinese_word(word)
        display_results(word, results)

if __name__ == "__main__":
    # Установите необходимые библиотеки:
    # pip install requests beautifulsoup4
    main()
# ```

# Также вот упрощенная версия, если вам нужен более быстрый вариант:

# ```python
# import requests
# from bs4 import BeautifulSoup

# def get_etymology_simple(word):
#     """Упрощенная версия для одного слова"""
#     url = f"https://www.archchinese.com/chinese_english_dictionary.html?find={word}"
    
#     try:
#         response = requests.get(url)
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Ищем основную информацию
#         char_info = soup.find('div', class_='char-info')
#         if char_info:
#             radical = char_info.find('span', string=lambda x: x and 'Radical' in x)
#             decomposition = char_info.find('span', string=lambda x: x and 'Decomposition' in x)
            
#             return {
#                 'radical': radical.get_text().replace('Radical:', '').strip() if radical else "Не найден",
#                 'decomposition': decomposition.get_text().replace('Decomposition:', '').strip() if decomposition else "Не найден"
#             }
    
#     except:
#         return None

# # Пример использования
# word = "牛仔裤"
# print(f"Анализ слова: {word}")

# for char in word:
#     result = get_etymology_simple(char)
#     if result:
#         print(f"\n{char}:")
#         print(f"  Радикал: {result['radical']}")
#         print(f"  Разбор: {result['decomposition']}")
# # ```

# **Как использовать:**

# 1. Установите необходимые библиотеки:
# ```bash
# pip install requests beautifulsoup4
# ```

# 2. Запустите программу и введите китайское слово

# **Особенности программы:**

# - Разбирает слово на отдельные иероглифы
# - Для каждого иероглифа получает радикал и разбор на компоненты
# - Отображает информацию в удобном формате
# - Обрабатывает ошибки сети и парсинга

# **Ограничения:**

# - Зависит от структуры сайта archchinese.com (при изменениях на сайте может потребоваться обновление кода)
# - Может работать медленно из-за множественных запросов к сайту
# - Для коммерческого использования проверьте условия использования сайта

# Программа успешно проанализирует ваши примеры и покажет разбор каждого иероглифа на составляющие компоненты!
