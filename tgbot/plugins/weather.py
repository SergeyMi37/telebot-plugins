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
from tgbot.handlers.utils.decorators import check_groupe_user
#from tgbot.handlers.utils import files
from users.models import User, Location
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
from tgbot.plugins import wiki, weather2png
from tgbot.handlers.admin.utils import get_day_of_week
from datetime import date, timedelta

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
    try:
        dadata = Dadata(token)
        result = dadata.geolocate(name="address", lat=lat, lon=lon)
        if result:
            val = result[0]['value'] # первый ближайший адрес
        else:
            val = ''
    except Exception as e:
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

def convert_date_format(date_str):
    '''
     # ДДММГГГГ --> ГГГГ-ММ-ДД
    '''
    day = date_str[:2]
    month = date_str[2:4]
    year = date_str[4:]
    return f"{year}-{month}-{day}"

def get_hourly_temperature(latitude, longitude, date ):
    start_date = end_date = f"{convert_date_format(date)}" # ДДММГГГГ
    url = f'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': ['temperature_2m', 'precipitation'],
        'start_date': start_date,
        'end_date': end_date
    }
    response = requests.get(url, params=params)
    data = response.json()
    out = ''
    hours = [] 
    day_temps = []
    night_temps = []
    precipitations = []
    if 'hourly' in data:
        temperatures = data['hourly']['temperature_2m']
        precipitation = data['hourly']['precipitation']  # Осадки
        timestamps = data['hourly']['time']

        for i in range(len(timestamps)):
            hour = timestamps[i].split('T')[1][:2]
            hours.append(hour)
            day_temps.append(temperatures[i])
            precipitations.append(precipitation[i])
            #out += (f' {hour} : {temperatures[i]}°C, Осадки {precipitation[i]} мм')
    else:
        out += 'Ошибка получения данных.'
    buf = weather2png.create_smooth_weather_chart(day_temps, night_temps, precipitations, hours, f' за {start_date} по часам' )
    return out, buf



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

def print_forecast(forecast, city_name,lat,lon):
    """Вывод прогноза погоды в читаемом формате"""
    out=""
    if not forecast or "daily" not in forecast:
        out += (f"\nДанные для {city_name} недоступны")
        return out

    out += (f"\n🌞Прогноз погоды для: {city_name}")
    out += (f" Часовой пояс: {forecast['timezone_abbreviation']} (UTC{forecast['utc_offset_seconds']//3600:+d})")
    day_temps = []
    night_temps = []
    precipitations = []
    days = []
    spo = ''
    for i, date in enumerate(forecast["daily"]["time"]):
        dt = datetime.fromisoformat(date)
        ddmmyyyy = dt.strftime('%d.%m.%Y')
        mark = "🔴" if get_day_of_week(ddmmyyyy,1) in [5,6] else ("🟠" if get_day_of_week(ddmmyyyy,1) in [4] else "⚪️")
        out += (f"\n{mark}📆{ddmmyyyy} {'завтра' if i == 1 else 'сегодня' if i == 0 else ''}")
        out += f'<b> {get_day_of_week(ddmmyyyy)}</b>'
        days.append(f'{get_day_of_week(ddmmyyyy)}\n{ddmmyyyy}')
        if spo =='':
            spo = f'с {ddmmyyyy}'
        #out += (f"\nМакс. температура: {forecast['daily']['temperature_2m_max'][i]}°C")
        #out += (f"\nМин. температура: {forecast['daily']['temperature_2m_min'][i]}°C")
        #/weather_houry_2025v06v30_55v75_37v62
        if i == 1 or i == 0:
            out += f'\n /weather_houry_{ddmmyyyy.replace(".","")}_{str(lat).replace(".","v")}_{str(lon).replace(".","v")}'
        out += (f"\n   c {forecast['daily']['temperature_2m_min'][i]} по {forecast['daily']['temperature_2m_max'][i]} °C")
        out += (f" {decode_weather(forecast['daily']['weathercode'][i])}")
        out += (f" Осадки: {forecast['daily']['precipitation_sum'][i]} мм")
        
        day_temps.append(forecast['daily']['temperature_2m_max'][i])
        night_temps.append(forecast['daily']['temperature_2m_min'][i])
        precipitations.append(forecast['daily']['precipitation_sum'][i])
    spo += f' по {ddmmyyyy}'
    out += ("\n")
    
    # _dir = os.path.join(files.media_dir, cid)
    # if not os.path.exists(_dir):
    #     os.mkdir(_dir)
    # filepng = os.path.join(_dir, f'{file_name}')
    #temps = []
    buf = weather2png.create_smooth_weather_chart(day_temps, night_temps, precipitations, days, ' за неделю '+spo )
    return out, buf

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
            return ou, None
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
    # ?pt=37.393269,55.029111;37.5,55.75  # ~ через тильду
    st, summ, link = wiki.fetch_page_data(city)
    wikiname = f"<a href=\"{link}\">{city}</a>" if st == 200 else city
    links = f"{wikiname} 🌎<a href=\"{url}\">({title} {str(lat)[:5]},{str(lon)[:5]})</a>"
    # Выводим 7-дневный прогноз
    if forecast_7days:
        _ou, buf = print_forecast(forecast_7days, f"{links} (7 дней)",lat,lon)
    else:
        _ou = f"{links})"
        buf = None
    ou += _ou
    return ou, buf

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = "Введите команду прогноза погоды"
    text += '\n\r🔸/help /weather'
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    cmd = telecmd.split('weather')[1]
    buf = None
    #/weater_Moscow в Москве на день и 7 дней. /weater_Piter /weater_Eburg /weater_Ludwigshafen
    if cmd.lower()=='_moscow':
       _out, buf = get_forecast("Moscow")
    elif cmd=='':
       #  получить последнюю запись для пользователя
       #last_location = Location.objects.filter(user_id=u.user_id).latest('created_at')
        if Location.objects.filter(user_id=u.user_id).exists():
            last_location = Location.objects.filter(user_id=u.user_id).latest('created_at')
            place = get_adress(last_location.latitude,last_location.longitude)
            st, place2 = reverse_geocode(last_location.latitude,last_location.longitude)
            if st==200:
                place += f".{place2}"
            else:
                print(place2)
            _out, buf = get_forecast(".",last_location.latitude,last_location.longitude,f"Ваше местоположение {place}")
            _out +=  "Обновить местоположение командой 📍/ask_location"
        else:
            _out = 'Для прогноза погоды по вашей геолокации предоставьте её командой 📍/ask_location'
    elif cmd.lower()=='_list':
       _out = f"/weather_Moscow в Москве на день и 7 дней. /weather_Piter /weather_Eburg <code>/weather_Серпухов</code> <code>/weather_Екатеринбург</code> <code>/weather_Нея</code>"
    elif cmd.lower()=='_piter':
       _out, buf = get_forecast("Piter")
    elif '_houry_' in cmd.lower(): # /weather_houry_2025v06v30_55v75_37v62
       current_date = cmd.lower().split("_")[2] # ДДММГГГГ
       lat = cmd.lower().split("_")[3].replace("v",".")
       lon = cmd.lower().split("_")[4].replace("v",".")
       _out, buf = get_hourly_temperature(lat, lon, current_date )
    elif cmd.lower()=='_eburg':
       _out, buf = get_forecast("Екатеринбург")
    elif cmd.lower()=='_test':
       link="https://yandex.ru/maps/?l=map&pt=55.7558,37.6173,Москва1111111~59.9343,30.3351,Санкт22222222" # &rtm_layer=&rtm_source=constructorLink"
       _out = f"<a href=\"{link}\">тест</a>"
    else:
        _out, buf = get_forecast(cmd.replace('_',''))
        #_out = f"По городу {cmd} еще нет геолокации"
    #print(_out)
    _out += '\n\r🔸/help /weather'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_out,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    if buf:
        context.bot.send_photo(chat_id=upms.chat.id, photo=buf)