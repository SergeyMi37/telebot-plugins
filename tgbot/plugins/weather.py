# Name Plugin: 
    # - WEATHER:
    #     desc = Погода  Москве на день и 10 дней. Введи команду, например /weater moscow 10

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_blocked_user
from users.models import User
import requests
from datetime import datetime, timedelta

# Добавить проверку на роль ''
plugin_wiki = get_plugins('').get('WEATHER')

def get_weather_forecast(latitude, longitude, days=1):
    """Получение прогноза погоды на указанное количество дней"""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=auto"
        f"&forecast_days={days}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None

def decode_weather(code):
    """Расшифровка кодов погоды"""
    weather_codes = {
        0: "Ясно",
        1: "Преимущественно ясно",
        2: "Переменная облачность",
        3: "Пасмурно",
        45: "Туман",
        48: "Инейный туман",
        51: "Легкая морось",
        53: "Умеренная морось",
        55: "Сильная морось",
        56: "Ледяная морось",
        57: "Сильная ледяная морось",
        61: "Небольшой дождь",
        63: "Умеренный дождь",
        65: "Сильный дождь",
        66: "Ледяной дождь",
        67: "Сильный ледяной дождь",
        71: "Небольшой снег",
        73: "Умеренный снег",
        75: "Сильный снег",
        77: "Снежные зерна",
        80: "Небольшие ливни",
        81: "Умеренные ливни",
        82: "Сильные ливни",
        85: "Снежные ливни",
        86: "Сильные снежные ливни",
        95: "Гроза",
        96: "Гроза с градом",
        99: "Сильная гроза с градом"
    }
    return weather_codes.get(code, "Неизвестный код")

def print_forecast(forecast, city_name):
    """Вывод прогноза погоды в читаемом формате"""
    out=""
    if not forecast or "daily" not in forecast:
        out += (f"\nДанные для {city_name} недоступны")
        return out

    out += (f"\n🌞Прогноз погоды для: {city_name}")
    out += (f"\n🕐Часовой пояс: {forecast['timezone_abbreviation']} (UTC{forecast['utc_offset_seconds']//3600:+d})")
    
    for i, date in enumerate(forecast["daily"]["time"]):
        dt = datetime.fromisoformat(date)
        out += (f"\n📆{dt.strftime('%d.%m.%Y')} ({'завтра' if i == 1 else 'сегодня' if i == 0 else date})")
        out += (f"\nПогода: {decode_weather(forecast['daily']['weathercode'][i])}")
        out += (f"\nМакс. температура: {forecast['daily']['temperature_2m_max'][i]}°C")
        out += (f"\nМин. температура: {forecast['daily']['temperature_2m_min'][i]}°C")
        out += (f"\nОсадки: {forecast['daily']['precipitation_sum'][i]} мм")
    out += ("\n")
    return out

# Координаты городов
def decode_cities(name):
    cities = {
        "Москва": (55.7558, 37.6173),
        "Санкт-Петербург": (59.9343, 30.3351),
        "Людвигсхафен": (49.4811, 8.4353)
    }
    return cities.get(name, "Неизвестный пока город")

def get_forecast(city):
    ou=""
    cities = {
        "Moscow": (55.7558, 37.6173),
        "Piter": (59.9343, 30.3351),
        "Eburg": (56,8519, 60,6122),
        "Ludwigshafen": (49.4811, 8.4353)
    }
    if cities.get(city,'')=='':
        ou += "По городу {cmd} еще нет геолокации."
        return ou
    # Получение и вывод прогноза для каждого города
    else:
        lat = cities[city][0]
        lon = cities[city][1]
    #for city, (lat, lon) in cities.items():
        # Прогноз на завтра (2 дня: сегодня+завтра)
        forecast_tomorrow = get_weather_forecast(lat, lon, days=2)
        # Прогноз на 7 дней
        forecast_7days = get_weather_forecast(lat, lon, days=7)
        
        # Выводим только завтрашний день из первого прогноза
        if forecast_tomorrow and "daily" in forecast_tomorrow:
            tomorrow_forecast = {
                "timezone_abbreviation": forecast_tomorrow["timezone_abbreviation"],
                "utc_offset_seconds": forecast_tomorrow["utc_offset_seconds"],
                "daily": {
                    key: [value[1]]  # Берем только данные за завтра (индекс 1)
                    for key, value in forecast_tomorrow["daily"].items()
                }
            }
            ou += print_forecast(tomorrow_forecast, f"{city} (Завтра)")
        
    # Выводим 7-дневный прогноз
    if forecast_7days:
        ou += print_forecast(forecast_7days, f"{city} (7 дней)")
    return ou

@check_blocked_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    u = User.get_user(update, context)
    text = "Введите слово или фразу..."
    text += '\n\r/help /wiki'
    context.bot.edit_message_text(
        text=text,
        chat_id=u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    cmd = telecmd.split('weather')[1]
    #/weater_Moscow в Москве на день и 7 дней. /weater_Piter /weater_Eburg /weater_Ludwigshafen
    if cmd=='_Moscow':
       _out = get_forecast("Moscow")
    elif cmd=='':
       _out = 'у вас нет геолокации, для посылки команда /ask_for_location'
    elif cmd=='_list':
       _out = 'todo'
    elif cmd=='_Piter':
       _out = get_forecast("Piter")
    elif cmd=='_Eburg':
       _out = get_forecast("Eburg")
    elif cmd=='_Ludwigshafen':
       _out = get_forecast("Ludwigshafen")
    else:
        _out = f"По городу {cmd} еще нет геолокации"
    #print(_out)
    _out += '\n\r/help /weather'
    context.bot.send_message(
        chat_id=u.user_id,
        text=_out,
        parse_mode=ParseMode.HTML
    )