# Name Plugin: CODE
    # - CODE:
    #     - desc = Поиск Регионов РФ по госномерам, поиск страны по началу штихкода на продуктах
# имя плагина CODE должно совпадать с именем в конфигурации Dynaconf
# имя плагина code должно быть первым полем от _ в имени файла code_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class CodPlugin(BasePlugin):
#    def setup_handlers(self, dp):
# https://codificator.ru/code/mobile/#list - полезный сайт

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
from tgbot.plugins.base_plugin import BasePlugin
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

# Добавить проверку на роль ''
plugin_wiki = get_plugins('').get('CODE')

CODE_INPUT = range(1)
#CODE_INPUT_EAN = range(1)
_code_help = "Введите команду например:\n\r /code_rf_01 или <code>/code_rf_Курс</code> - получить название региона по коду или код по началу названия" \
        "\n\r /code_ean_46 или <code>/code_ean_Кита</code> - получить название страны по штрихкоду или код по началу названия" \
        "\n\r /code_ean_ - получить все штрихкоды \n\r/code_rf_ - получить название всех регионов" \
        "\n\r /code_ean - ввести контекст штрихкодов \n\r/code_rf - ввести контекст названий регионов" 
 
def request_code_ean(update: Update, context):
    """Запрашиваем код у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите 2 или 3 цифры штрихкода или имя страны /cancel - отмена")
    return CODE_INPUT #_EAN

def check_code_ean(update: Update, context):
    """Проверяем введённый штрихкод """
    upms = get_tele_command(update)
    code = upms.text
    _name = find_country(code)
    if _name:
        response = f"ШтрихКод '{code}' соответствует стране {_name}"
    else:
        response = f"ШтрихКод '{code}' неизвестен."
    #upms.reply_text(response)
    context.bot.send_message(
        chat_id=upms.chat.id,
        text = response + '\n\r🔸/help /code',
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def request_code(update: Update, context):
    """Запрашиваем код у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите 2 или 3 цифры кода или наименование региона РФ /cancel - отмена")
    return CODE_INPUT

def check_code(update: Update, context):
    """Проверяем введённый код региона"""
    upms = get_tele_command(update)
    code = upms.text
    region_name = find_region(code)
    if region_name:
        response = f"Код региона '{code}' соответствует городу/региону {region_name}"
    else:
        response = f"Код региона '{code}' неизвестен."
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=response + '\n\r🔸/help /code',
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("Операция отменена.")
    return ConversationHandler.END

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

class CodPlugin(BasePlugin):
    def setup_handlers(self, dp):
        cmd = "/code"

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('code_rf', request_code)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_code),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
            ]
        )
        conv_handler_ean = ConversationHandler(
            entry_points=[CommandHandler('code_ean', request_code_ean)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_code_ean),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
            ]
        )

        dp.add_handler(conv_handler)
        dp.add_handler(conv_handler_ean)
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands))
        dp.add_handler(MessageHandler(Filters.regex(rf'^code(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button, pattern="^button_code"))

regions = {
        "01,101": "Республика Адыгея",
        "02,102,702": "Республика Башкортостан",
        "03,103": "Республика Бурятия",
        "04": "Республика Алтай",
        "05": "Республика Дагестан",
        "06": "Республика Ингушетия",
        "07": "Кабардино-Балкарская Республика",
        "08": "Республика Калмыкия",
        "09,109": "Карачаево-Черкесская Республика",
        "10": "Республика Карелия",
        "11,111": "Республика Коми",
        "12": "Республика Марий Эл",
        "13,113": "Республика Мордовия",
        "14": "Республика Саха (Якутия)",
        "15": "Республика Северная Осетия — Алания",
        "16,116,716": "Республика Татарстан",
        "17": "Республика Тыва",
        "18,118": "Удмуртская Республика",
        "19": "Республика Хакасия",
        "20,95": "Чеченская Республика (до 2000 года)",
        "21,121": "Чувашская Республика",
        "22,122": "Алтайский край",
        "23,93,123,193,323": "Краснодарский край",
        "24,84,88,124": "Красноярский край",
        "25,125,725": "Приморский край",
        "26,126": "Ставропольский край",
        "27": "Хабаровский край",
        "28": "Амурская область",
        "29": "Архангельская область",
        "30,130": "Астраханская область",
        "31": "Белгородская область",
        "32": "Брянская область",
        "33": "Владимирская область",
        "34,134": "Волгоградская область",
        "35": "Вологодская область",
        "36,136": "Воронежская область",
        "37": "Ивановская область",
        "38,138": "Иркутская область",
        "39,91,139": "Калининградская область",
        "40": "Калужская область",
        "41": "Камчатский край",
        "42,142": "Кемеровская область (Кузбас)",
        "43": "Кировская область",
        "44": "Костромская область",
        "45": "Курганская область",
        "46": "Курская область",
        "47,147": "Ленинградская область",
        "48": "Липецкая область",
        "49": "Магаданская область",
        "50,90,150,190,250,550,750,790": "Московская область",
        "51": "Мурманская область",
        "52,152,252": "Нижегородская область",
        "53": "Новгородская область",
        "54,154,754": "Новосибирская область",
        "55,155": "Омская область",
        "56,156": "Оренбургская область",
        "57": "Орловская область",
        "58,158": "Пензенская область",
        "59,159": "Пермский край",
        "60": "Псковская область",
        "61,161,761": "Ростовская область",
        "62": "Рязанская область",
        "63,163,763": "Самарская область",
        "64,164": "Саратовская область",
        "65": "Сахалинская область",
        "66,96,196": "Свердловская область (Екатеринбург)",
        "67": "Смоленская область",
        "68": "Тамбовская область",
        "69,169": "Тверская область",
        "70": "Томская область",
        "71": "Тульская область",
        "72,172": "Тюменская область",
        "73,173": "Ульяновская область",
        "74,175,774": "Челябинская область",
        "75": "Забайкальский край",
        "76": "Ярославская область",
        "77,97,99,177,197,199,777,797,799,977": "Москва",
        "78,98,178,198": "Санкт-Петербург",
        "79": "Еврейская автономная область",
        "80,180": "Донецкая Народная Республика (ДНР)",
        "81,191": "Луганская Народная Республика (ЛНР)",
        "82,182": "Республика Крым",
        "83": "Ненецкий автономный округ",
        "84,184": "Херсонская область",
        "85,185": "Запорожская область",
        "86,186": "Ханты-Мансийский автономный округ — Югра",
        "87": "Чукотский автономный округ",
        "88": "Красноярский край (старый код)",
        "89": "Ямало-Ненецкий автономный округ",
        "90": "Московская область (старый код)",
        "91": "Калининградская область (старый код)",
        "92,192": "Севастополь",
        "93": "Краснодарский край (включая Адыгею)",
        "94": "Территории за пределами РФ (Байконур)",
        "188": "Харьковская область"
    }

COUNTRY_CODES = {
    "0-13": "США и Канада",
    "30-37": "Франция",
    "380": "Болгария",
    "383": "Словения",
    "385": "Хорватия",
    "387": "Босния и Герцеговина",
    "400-440": "Германия",
    "45": "Япония",
    "49": "Япония",
    "460-469": "Россия",
    "471": "Тайвань",
    "474": "Эстония",
    "475": "Латвия",
    "476": "Азербайджан",
    "477": "Литва",
    "478": "Узбекистан",
    "479": "Шри-Ланка",
    "480": "Филиппины",
    "481": "Беларусь",
    "482": "Украина",
    "484": "Молдова",
    "485": "Армения",
    "486": "Грузия",
    "487": "Казахстан",
    "489": "Гонконг",
    "50": "Великобритания",
    "520-521": "Греция",
    "528": "Ливан",
    "529": "Кипр",
    "530": "Албания",
    "531": "Македония",
    "535-539": "Мальта",
    "54": "Бельгия и Люксембург",
    "560": "Португалия",
    "569": "Исландия",
    "57": "Дания",
    "590": "Польша",
    "594": "Румыния",
    "599": "Венгрия",
    "600-601": "Южная Африка",
    "609": "Маврикий",
    "611": "Марокко",
    "613": "Алжир",
    "619": "Тунис",
    "621": "Сирия",
    "622": "Египет",
    "624": "Ливия",
    "625": "Иордания",
    "626": "Иран",
    "627": "Кувейт",
    "628": "Саудовская Аравия",
    "629": "ОАЭ",
    "64": "Финляндия",
    "690-695": "Китай",
    "70": "Норвегия",
    "729": "Израиль",
    "73": "Швеция",
    "740-745": "Центральная Америка (Гватемала, Сальвадор, Гондурас)",
    "750": "Мексика",
    "759": "Венесуэла",
    "76": "Швейцария",
    "770-771": "Колумбия",
    "773": "Уругвай",
    "775": "Перу",
    "777": "Боливия",
    "779": "Аргентина",
    "780": "Чили",
    "784": "Парагвай",
    "786": "Эквадор",
    "789-790": "Бразилия",
    "80-83": "Италия",
    "84": "Испания",
    "850": "Куба",
    "858": "Словакия",
    "859": "Чехия",
    "860": "Сербия",
    "865": "Монголия",
    "867": "Северная Корея",
    "869": "Турция",
    "87": "Нидерланды",
    "880": "Южная Корея",
    "885": "Таиланд",
    "888": "Сингапур",
    "890": "Индия",
    "893": "Вьетнам",
    "896": "Пакистан",
    "899": "Индонезия",
    "90-91": "Австрия",
    "93": "Австралия",
    "94": "Новая Зеландия",
    "955": "Малайзия",
    "958": "Макао",
    "977": "Международные периодические издания (ISSN)",
    "978-979": "Международные книжные номера (ISBN)",
    "980": "Возвратные купонные системы",
    "981-982": "Общие товары международного уровня (Валютные купоны)",
    "990-999": "Купоны"
    }

# Функция для извлечения первого диапазона чисел из строки
def extract_prefix(barcode):
    for key,val in COUNTRY_CODES.items():
        if ('-' not in key and int(key) == int(barcode) ) or ('-' in key and int(key.split('-')[0]) <= int(barcode) <= int(key.split('-')[1])):
            #print(key,val)
            return key
    return None

# Основная функция определения региона
def find_region(input_data):
    '''
    Проверяет код региона и возвращает его название
    Номера регионов России на автомобилях
    https://auto.ru/mag/article/avtomobilnye-kody-regionov-rossii/?utm_referrer=https%3A%2F%2Fwww.google.com%2F
    
    '''
    input_data = str(input_data).strip()  # Приводим входные данные к строке и удаляем пробелы
    found=""
    _input = input_data
    if input_data.isdigit():
        if len(input_data) > 3:
            _input = input_data[:3]
    for key,val in regions.items():
        if _input.isdigit():
            if f',{_input},' in f',{key},':
                found += f'\n\r<b>{key}</b> {val}'
        else:
            if input_data.lower() in val.lower():
                found += f'\n\r<b>{key}</b> {val}'
    if found=='':
        return "Регион не найден."
    return found


# Основная функция определения страны по штрих-коду или её названию
def find_country(input_data):
    '''
    Штрих коды стран производителей
    https://bosla.ru/poleznaya-informatsiya/pro-shtrikh-kod/shtrikh-kod
    '''
    input_data = str(input_data).strip()  # Приводим входные данные к строке и удаляем пробелы
    # Если ввод — число (штрих-код), проверяем его диапазон
    if input_data=='46':
        input_data = '460'
    _input = input_data
    if input_data.isdigit():
        if len(input_data) > 3:
            _input = input_data[:3]
    if _input.isdigit():
        prefix = extract_prefix(_input)
        if prefix is not None:
            return f'<b>{prefix}</b> {COUNTRY_CODES.get(prefix, "Страна неизвестна")}'
        else:
            return f'Штрих-код EAN, начинающийся на цифру "{input_data}", не найден в справочнике'
    found=""
    for key,val in COUNTRY_CODES.items():
        #if input_data.lower() in val.lower():
        if val.lower().startswith(input_data.lower()):
            found += f'\n\r<b>{key}</b> {val}'
    if found=='':
        return "Страна не найдена."
    return found

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    upms = get_tele_command(update)
    text = "Введите код региона автомобильного номера, или текст региона. Штрихкоды стран производителей"
    text += _code_help
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
    _input = telecmd.split('code')[1] #.replace("_"," ")
    _output = ""
    if "_rf_" in _input:
       _output = find_region(_input.split('_rf_')[1])
    elif "_ean_" in _input:
        _output = find_country(_input.split('_ean_')[1])
    else:
        _output = _code_help
    _output += '\n\r🔸/help /code'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
'''
Вот простой пример реализации двухэтапного диалога с использованием библиотеки Python telegram.ext, демонстрирующий пошаговую передачу двух параметров от пользователя:

Предположим, мы хотим собрать у пользователя название города и дату путешествия, чтобы предложить какую-нибудь полезную информацию о погоде или мероприятиях в выбранный период.

Шаги диалога:

Бот просит ввести город назначения.
Затем бот просит ввести желаемую дату путешествия.
После ввода обоих параметров, бот выводит итоговую информацию.

Код примера:

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Константы для обозначения этапов диалога
CITY, DATE = range(2)

def start(update: Update, context: CallbackContext) -> int:
    """Запускаем диалог"""
    update.message.reply_text("Привет! Напиши название города.")
    return CITY

def city_input(update: Update, context: CallbackContext) -> int:
    """Пользователь ввёл название города"""
    user_city = update.message.text
    context.user_data['city'] = user_city
    update.message.reply_text(f'Город {user_city}. Теперь напиши дату твоего путешествия.')
    return DATE

def date_input(update: Update, context: CallbackContext) -> None:
    """Пользователь ввёл дату путешествия"""
    travel_date = update.message.text
    context.user_data['date'] = travel_date
    chosen_city = context.user_data.get('city')
    update.message.reply_text(f"Твой выбор: {chosen_city}, {travel_date}. Спасибо!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> None:
    """Отмена диалога"""
    update.message.reply_text("Диалог отменён.")
    return ConversationHandler.END

def main():
    updater = Updater("ВАШ_TOKEN_БОТА")
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CITY: [MessageHandler(Filters.text & ~Filters.command, city_input)],
            DATE: [MessageHandler(Filters.text & ~Filters.command, date_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

Как работает?

Команда /start запускает первый этап диалога, предлагая пользователю ввести название города.
Получив название города, программа сохраняет его в памяти контекста (context.user_data) и предлагает ввести дату.
Получив дату, программа также сохраняет её и выводит итоговую информацию.
Для выхода из диалога предусмотрена команда /cancel.

Диалог выглядит примерно так:

Пользователь: /start
Бот: Привет! Напиши название города.
Пользователь: Москва
Бот: Город Москва. Теперь напиши дату твоего путешествия.
Пользователь: 1 июня
Бот: Твой выбор: Москва, 1 июня. Спасибо!

Или, если пользователь решает отменить диалог:

Пользователь: /start
Бот: Привет! Напиши название города.
Пользователь: /cancel
Бот: Диалог отменён.

Теперь у вас есть рабочий шаблон для сбора нескольких последовательных параметров от пользователя.

'''