import io
import csv

from datetime import datetime
from django.db.models import QuerySet
from typing import Dict


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