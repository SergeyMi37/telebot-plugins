# Name Plugin: 
    # - WEATHER:
    #     desc = Погода  Москве на день и 10 дней. Введи команду, например /weater moscow 10
from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_blocked_user
from users.models import User, Location
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from tgbot.plugins import wiki
from tgbot.handlers.admin.utils import get_day_of_week

# Добавить проверку на роль ''
plugin_weather = get_plugins('').get('WEATHER')

# https://dadata.ru/api/geolocate/
# https://github.com/hflabs/dadata-py
from dadata import Dadata

# https://www.openstreetmap.org/  «Дадата» берет координаты домов и улиц из OpenStreetMap. 
def get_adress(lat,lon):
    token = plugin_weather.get('dadata_token','')
    if not token:
        return ''
    dadata = Dadata(token)
    result = dadata.geolocate(name="address", lat=lat, lon=lon)
    if result:
        val = result[0]['value'] # первый ближайший адрес
        #print('---',val)
    else:
        val = ''
    return val

def reverse_geocode(lat, lon):
    # Базовая ссылка API Nominatim
    base_url = 'https://nominatim.openstreetmap.org/reverse'
    # Параметры запроса
    params = {
        'format': 'json',       # Формат результата — JSON
        'lat': lat,             # Широта точки
        'lon': lon,             # Долгота точки
        'zoom': 18,             # Уровень детализации карты
        'addressdetails': 1     # Возвращение детальной адресной информации
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    #response = requests.get(url, headers=headers)
    try:
        response = requests.get(base_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            address = data['address']
            result = f"{address.get('road', '')}, {address.get('village', '')}, {address.get('city', '')}, {address.get('state', '')}, {address.get('country', '')}"
            return 200, result.strip(', ')
        else:
            return response.status_code, (f'Ошибка: {response.status_code}')

    except Exception as e:
        return 1, (f'Ошибка обработки запроса: {e}')


def get_coordinates(place_name):
    # Создаем объект-геокодера OpenStreetMap (Nominatim)
    geolocator = Nominatim(user_agent="geo_query")
    try:
        location = geolocator.geocode(place_name)
        if location is None:
            res = (f"Место '{place_name}' не найдено.")
            return res, 0, 0 
        else:
            latitude = location.latitude
            longitude = location.longitude
            return 200, latitude, longitude 
            #print(f"Координаты {place_name}: широта={latitude}, долгота={longitude}")
    
    except Exception as e:
        #print("Возникла ошибка:", str(e))
        return str(e), 0, 0 


def get_weather_forecast(latitude, longitude, days=1):
    """Получение прогноза погоды на указанное количество дней"""
    uri  = plugin_weather.get('url','')
    if not uri:
        print(f"Пустой параметр url в настройках dynaconf")
        return None
    url = (
        f"{uri}?"
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
        0: "☀️Ясно",
        1: "🌤Преимущественно ясно",
        2: "⛅️Переменная облачность",
        3: "🌥Пасмурно",
        45: "☁Туман",
        48: "☁💨Инейный туман",
        51: "💨Легкая морось",
        53: "💨💨Умеренная морось",
        55: "💨🔵Сильная морось",
        56: "💧Ледяная морось",
        57: "❄💧Сильная ледяная морось",
        61: "⛈Небольшой дождь",
        63: "🌂☔Умеренный дождь",
        65: "🌧☔Сильный дождь",
        66: "❄💧Ледяной дождь",
        67: "❄💧💧Сильный ледяной дождь",
        71: "❄️Небольшой снег",
        73: "🌨❄Умеренный снег",
        75: "🌨❄️❄Сильный снег",
        77: "❄❄️🔵Снежные зерна",
        80: "☔Небольшие ливни",
        81: "☔🌧Умеренные ливни",
        82: "☔☔🌧Сильные ливни",
        85: "❄☃️💧Снежные ливни",
        86: "❄️☃️💧Сильные снежные ливни",
        95: "⚡Гроза",
        96: "⚡🌩Гроза с градом",
        99: "⚡💧🌩Сильная гроза с градом"
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
        ddmmyyyy = dt.strftime('%d.%m.%Y')
        mark = "🔴" if get_day_of_week(ddmmyyyy,1) in [5,6] else "⚪️"
        out += (f"\n{mark}📆{ddmmyyyy} ({'завтра' if i == 1 else 'сегодня' if i == 0 else date})")
        out += f'<b> {get_day_of_week(ddmmyyyy)}</b>'
        out += (f"\n  {decode_weather(forecast['daily']['weathercode'][i])}")
        #out += (f"\nМакс. температура: {forecast['daily']['temperature_2m_max'][i]}°C")
        #out += (f"\nМин. температура: {forecast['daily']['temperature_2m_min'][i]}°C")
        out += (f"\n  {forecast['daily']['temperature_2m_min'][i]} - {forecast['daily']['temperature_2m_max'][i]} °C")
        out += (f"\n  Осадки: {forecast['daily']['precipitation_sum'][i]} мм")
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

def get_forecast(city,latitude=None,longitude=None,title=""):
    ou=""
    cities = {
        "Moscow": (55.7558, 37.6173),
        "Piter": (59.9343, 30.3351),
        "Eburg": (56,8519, 60,6122),
        "Ludwigshafen": (49.4811, 8.4353)
    }
    if latitude:
        lat = latitude
        lon = longitude
    elif cities.get(city,'')=='':
        st, lat, lon = get_coordinates(city)
        if not st == 200:
            ou += f"По городу {city} нет геолокации. {st}"
            return ou
    # Получение и вывод прогноза для каждого города 🌦 
    else:
        lat = cities[city][0]
        lon = cities[city][1]
    #for city, (lat, lon) in cities.items():
        # Прогноз на завтра (2 дня: сегодня+завтра)
        #forecast_tomorrow = get_weather_forecast(lat, lon, days=2)
        
        # Прогноз на 7 дней
    forecast_7days = get_weather_forecast(lat, lon, days=7)
        
        # Выводим только завтрашний день из первого прогноза
        # if forecast_tomorrow and "daily" in forecast_tomorrow:
        #     tomorrow_forecast = {
        #         "timezone_abbreviation": forecast_tomorrow["timezone_abbreviation"],
        #         "utc_offset_seconds": forecast_tomorrow["utc_offset_seconds"],
        #         "daily": {
        #             key: [value[1]]  # Берем только данные за завтра (индекс 1)
        #             for key, value in forecast_tomorrow["daily"].items()
        #         }
        #     }
        #     ou += print_forecast(tomorrow_forecast, f"{city} (Завтра)")
    
    #url = f"https://yandex.ru/maps/?ll={lon}%2C{lat}&z=11&l=map" # (8-20км, 10-6км 12-2км, 15-200м 17-60м,).
    url = f"https://yandex.ru/maps/?pt={lon},{lat}&z=11&l=map" # (8-20км, 10-6км 12-2км, 15-200м 17-60м,).
    # ?pt=37.393269,55.029111;37.5,55.75
    st, summ, link = wiki.fetch_page_data(city)
    wikiname = f"<a href=\"{link}\">{city}</a>" if st == 200 else city
    links = f"{wikiname} 🌎<a href=\"{url}\">({title} {str(lat)[:5]},{str(lon)[:5]})</a>"
    # Выводим 7-дневный прогноз
    if forecast_7days:
        ou += print_forecast(forecast_7days, f"{links} (7 дней)")
    else:
        ou += f"{links})"
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
    if cmd.lower()=='_moscow':
       _out = get_forecast("Moscow")
    elif cmd=='':
       #  получить последнюю запись для пользователя
       #last_location = Location.objects.filter(user_id=u.user_id).latest('created_at')
        if Location.objects.filter(user_id=u.user_id).exists():
            last_location = Location.objects.filter(user_id=u.user_id).latest('created_at')
            place = get_adress(last_location.latitude,last_location.longitude)
            st, place2 = reverse_geocode(last_location.latitude,last_location.longitude)
            if st==200:
                place += f"---{place2}"
            else:
                print(place2)
            _out = get_forecast(".",last_location.latitude,last_location.longitude,f"Ваше местоположение {place}")
            _out +=  "Обновить местоположение командой 📍/ask_location"
        else:
            _out = 'Для прогноза погоды по вашей геолокации предоставьте её командой 📍/ask_location'
    elif cmd.lower()=='_list':
       _out = f"/weather_Moscow в Москве на день и 7 дней. /weather_Piter /weather_Eburg /weather_Серпухов /weather_Екатеринбург /weather_Нея"
    elif cmd.lower()=='_piter':
       _out = get_forecast("Piter")
    elif cmd.lower()=='_eburg':
       _out = get_forecast("Екатеринбург")
    else:
        _out = get_forecast(cmd.replace('_',''))
        #_out = f"По городу {cmd} еще нет геолокации"
    #print(_out)
    _out += '\n\r/help /weather'
    context.bot.send_message(
        chat_id=u.user_id,
        text=_out,
        parse_mode=ParseMode.HTML
    )