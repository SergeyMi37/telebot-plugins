# Name Plugin: chinese_scool
    # - CHINESE_SCOOL:
    #     - desc = Сервис для скачивания роликов с Ютуба и ВкВидео и обмена ссылками между пользователями бота
# имя плагина MEDIA должно совпадать с именем в конфигурации Dynaconf
# имя плагина media должно быть первым полем от _ в имени файла media_plugin
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

    # Добавить проверку на роль ''
    #plugin_wiki = get_plugins_for_roles('').get('WIKI')

    plugin_cmd = "chinese_scool"
    CODE_INPUT = range(1)
    plugin_help = f'Учить китайские иероглифы. 🔸/help /{plugin_cmd} /{plugin_cmd}_ - введите иероглифы' 


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

# if __name__ == "__main__":
#     # Установите необходимые библиотеки:
#     # pip install requests beautifulsoup4
#     main()
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

import requests

def fetch_etymology(characters):
    base_url = 'https://hanzidb.org/api/v1'
    
    for char in characters:
        response = requests.get(f'{base_url}/characters/{char}')
        
        if response.status_code != 200:
            return f'Ошибка при получении данных для {char}'
            
        data = response.json()
        
        etymology_data = data['etymology']
        
        if not etymology_data:
            print(f'Нет этимологических данных для {char}.')
        else:
            origin = etymology_data.get('origin', '')
            structure = etymology_data.get('structure', {})
            print(f'\\nИероглиф: {char}\\nПроисхождение: {origin}\\nСтруктура: {structure}')

# if __name__ == '__main__':
#     chinese_word = '牛仔裤'
#     fetch_etymology(chinese_word)

# Понимаю, что вы ищете способы получения этимологии китайских иероглифов программным путём на Python. К сожалению, среди результатов поиска нет информации о конкретных API-сервисах, специализирующихся **исключительно на этимологии китайских иероглифов**, которые предоставляли бы готовые endpoint'ы для прямого запроса.

# Однако вы можете воспользоваться общими API для работы с китайскими иероглифами, которые часто включают информацию об их составе, значении, а иногда и исторической эволюции. Для иероглифа "牛仔裤" (niúzǎikù, джинсы) этимология скорее будет связана с историей слова и заимствованием, чем с древней формой самого иероглифа.

# Вот пример программы на Python, которая использует доступные API для получения информации об иероглифах. Поскольку прямых API этимологии может не быть, мы будем использовать общие API китайского языка и парсить информацию.

# ```python
import requests

def get_character_etymology(character):
    """
    Функция для получения информации об иероглифе. 
    Поскольку прямого API для этимологии может не быть, 
    эта функция использует общий API для китайских иероглифов.
    """
    # Пример API: HanziDB (неофициальный API) или другие подобные сервисы
    url = f"https://hanzidb.org/character/{character}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        
        # Здесь вам нужно будет проанализировать HTML-ответ, 
        # так как HanziDB не предоставляет чистого JSON API.
        # Это просто пример; фактический парсинг будет сложнее.
        if response.status_code == 200:
            # Предположим, что мы нашли блок с этимологией (это зависит от структуры сайта)
            # В реальности нужно использовать BeautifulSoup для парсинга HTML
            print(f"Информация для иероглифа '{character}' найдена на HanziDB.")
            print(f"URL: {url}")
            # Поскольку фактический парсинг выходит за рамки простого примера, 
            # рекомендуется посмотреть документацию HanziDB или использовать другие API.
        else:
            print(f"Не удалось получить данные для иероглифа '{character}'.")
    except requests.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")

def get_word_etymology(word):
    """
    Функция для получения этимологии слова (например, 牛仔裤).
    В данном случае это может быть сложно, так как этимология слова 
    часто связана с историей и заимствованиями, а не только с иероглифами.
    """
    # Для слов этимология может быть найдена в словарях или специализированных ресурсах.
    # Один из способов — использовать API словарей, например, Line Dictionary или others.
    url = f"https://dict.co.ua/search/?q={word}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Аналогично, парсинг HTML-ответа.
        if response.status_code == 200:
            print(f"Информация о слове '{word}' найдена в словаре.")
            print(f"URL: {url}")
        else:
            print(f"Не удалось найти информацию о слове '{word}'.")
    except requests.RequestException as e:
        print(f"Ошибка при запросе к словарю: {e}")

# Основная программа
if __name__ == "__main__":
    input_word = "牛仔裤"
    print(f"Получение информации для слова: {input_word}")
    
    # Для слова "牛仔裤" мы можем попытаться найти общую информацию
    get_word_etymology(input_word)
    
    # Если вы хотите разобрать слово на иероглифы и получить информацию по каждому
    characters = list(input_word)
    for char in characters:
        print(f"\nПолучение информации для иероглифа: {char}")
        get_character_etymology(char)

# **Важные замечания:**

# 1.  **Отсутствие прямого API:** Прямых API для получения этимологии иероглифов может не быть. Многие ресурсы предоставляют информацию через веб-интерфейс, что требует парсинга HTML (например, с помощью `beautifulsoup4`). В примере выше используется условный URL HanziDB, но вам нужно проверить актуальность и возможность использования такого подхода.
# 2.  **Парсинг веб-страниц:** Если вы решите парсить веб-сайты, обязательно ознакомьтесь с их `robots.txt` и условиями обслуживания. Не все сайты приветствуют автоматизированные запросы.
# 3.  **Альтернативные подходы:**
#     *   **Локальные базы данных:** Некоторые проекты предлагают базы данных с этимологией иероглифов (например, в формате JSON или SQLite). Это может быть надежнее, чем полагаться на веб-API.
#     *   **Специализированные библиотеки:** Для Python есть библиотеки, такие как `zhon` для работы с китайским текстом, но они обычно не содержат полной этимологической информации.
#     *   **Использование образовательных ресурсов:** Некоторые онлайн-платформы или приложения (например, "Дворец Китайского Языка" ) могут иметь структурированные данные, но доступ через API может быть ограничен.

# **Рекомендации:**

# 1.  **Исследуйте доступные API:** Посмотрите в сторону таких ресурсов, как **HanziDB**, **Arch Chinese**, **YellowBridge**, но проверяйте, предоставляют ли они официальное API.
# 2.  **Используйте словарные API:** Для слов (а не отдельных иероглифов) могут подойти API словарей, например, **Pleco** (у них есть SDK для разработчиков) или **Line Dictionary**.
# 3.  **Рассмотрите парсинг с осторожностью:** Если API нет, а информация очень нужна, можно аккуратно парсить сайты, соблюдая правила и ограничивая частоту запросов.

# Для получения точной и достоверной информации об этимологии китайских иероглифов часто требуется обращаться к специализированной литературе и академическим ресурсам, которые не всегда доступны через простые API.