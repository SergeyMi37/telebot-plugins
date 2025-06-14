
from datetime import datetime
from django.db.models import QuerySet
from typing import Dict
from pathlib import Path
from dtb.settings import DATABASE_URL, DEBUG
import os, socket, platform, requests, io, csv

def get_day_of_week(date_string):
    """ Преобразование строки даты в объект datetime 
        Пример использования:
        print(get_day_of_week("2023-10-25"))  # Выведет "Среда"
        print(get_day_of_week("26.10.2023"))  # Выведет "Четверг"
    """
    date_obj = datetime.strptime(date_string, "%d.%m.%Y") if "." in date_string else datetime.strptime(date_string, "%Y-%m-%d")
    # Список русских названий дней недели
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    # Возвращаем день недели по индексу
    return days[date_obj.weekday()]

def _get_csv_from_qs_values(queryset: QuerySet[Dict], filename: str = 'users'):
    keys = queryset[0].keys()
    print('--csvkeys-',type(keys),keys)
    print('--csv-',type(queryset),queryset)
    # csv module can write data in io.StringIO buffer only
    s = io.StringIO()
    dict_writer = csv.DictWriter(s, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows(queryset)
    s.seek(0)

    # python-telegram-bot library can send files only from io.BytesIO buffer
    # we need to convert StringIO to BytesIO
    buf = io.BytesIO()

    # extract csv-string, convert it to bytes and write to buffer
    buf.write(s.getvalue().encode())
    buf.seek(0)

    # set a filename with file's extension
    buf.name = f"{filename}__{datetime.now().strftime('%Y.%m.%d.%H.%M')}.csv"

    return buf

def piece(value,  *args, **kwargs):
    if not value: return ""
    delimiter = kwargs['delimiter']
    num = kwargs['num']
    return value.split(delimiter)[num]  # $piece(a,"*",num)

def iris_piece(value, delim, num):
    if not value: return ""
    return value.split(delim)[num]  # txt.split(" ")[1::])) # $piece(a," ",2,

class GetExtInfo:
    """Класс для получения дополнительной информации."""

    @staticmethod
    def GetGitInfo():
        """Получить расширенную информацию о месте запуска программы и ветки Гита"""
        # Получить родительский путь запуска программы
        dir = str(Path(os.getcwd()).resolve()) # .parent)
        # Найти файл с информацией о ветках проекта
        fn = os.path.join(dir + "/.git", "config")
        fnind = os.path.join(dir + "/.git", "index")
       
        if os.path.exists(fn):
            with open(fn, 'r') as file:
                # получить время последней модификации файла
                fn_datatime = f"📆 { (datetime.fromtimestamp(os.path.getmtime(fnind)) )}"
                content = file.read()
                dir += f"\n 🌴 Последняя ветка [{content.split('[branch ')[content.count('[branch ')]}  {fn_datatime}"
        return f"\n 🚧 Режим отладки: {DEBUG}\n 🅿 DATABASE_URL :{DATABASE_URL}\n 📂 Каталог проекта {dir}"

    @staticmethod
    def GetHostInfo():
        """Получить расширенную информацию о хосте и IP"""
        # Получаем имя хоста
        hostname = socket.gethostname()
        # Получаем локальный IP адрес (IPv4)
        ip_address = socket.gethostbyname(hostname)
        #print(f'IP адрес: {ip_address}')
        return f"\n 🔳 Имя хоста: {hostname}\n 🔳 IP адрес: {ip_address}"

    @staticmethod
    def GetExtIp():
        """Получить внешний IP"""
        # Получаем глобального адреса
        url = 'https://api.ipify.org/'
        response = requests.get(url,verify=False) #,headers=headers,timeout=timeout,auth=auth)
        #print(response.text)
        return f"\n 🌐 IP адрес: {response.text}"

    @staticmethod
    def GetOS():
        """Получить информацию о ОС"""
        # Получаем имя и версию ОС
        os_name = platform.system()
        os_version = platform.release()
        return (f"\n⭕ ОС: {os_name}, версия: {os_version}")