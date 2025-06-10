import io
import csv

from datetime import datetime
from django.db.models import QuerySet
from typing import Dict

import os
from pathlib import Path
from dtb.settings import DATABASE_URL


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
        print(fn)
    
        if os.path.exists(fn):
            with open(fn, 'r') as file:
                # получить время последней модификации файла
                fn_datatime = f"📆 **{ (datetime.fromtimestamp(os.path.getmtime(fn)) )}**"
                content = file.read()
                dir += f"\n 🌴 **Последняя ветка** [{content.split('[branch ')[content.count('[branch ')]}  {fn_datatime}"
        return f"\n 🚧 **Режим отладки.**\n 🅿 DATABASE_URL : //{DATABASE_URL}\n 📂 **Каталог проекта** {dir}"
    
    