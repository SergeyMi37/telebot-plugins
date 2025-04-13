from typing import Any
from datetime import datetime, timedelta
import pytz
DATETIME_TEMPLATE = "%Y.%m.%d %H:%M:%S"
DATE_TEMPLATE = "%Y.%m.%d"
DATETIME_MIN_LENGHT = 10

# приведение строки 2024-07-31T20:00:00Z к объекту date() мск времени
def tz_to_moscow(date_time: str) -> datetime:
    if 'T20:00:00Z' in date_time:
      date_time = date_time.replace('T20:00:00Z','T21:00:00Z') 
    if 'T17:00:00Z' in date_time:
      date_time = date_time.replace('T17:00:00Z','T21:00:00Z')
    if 'T18:00:00Z' in date_time:
      date_time = date_time.replace('T18:00:00Z','T21:00:00Z')
    dt = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%SZ')
    moscow_tz = pytz.timezone('Europe/Moscow')
    dt_utc = dt.replace(tzinfo=pytz.UTC)
    dt_moscow = dt_utc.astimezone(moscow_tz)
    #output_string = dt_moscow.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    return dt_moscow.date()

def str_to_date(date_str: str) -> datetime:
  return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def dump_datetime(value) -> list[Any] | None:
  """
  Функция преобразования datetime в строку установленного формата
  :param value: datetime
  :return:
  """
  try:
    if value is None:
      return None
    else:
      return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
  except:
    return None


def dump_datetime_to_str(value, separator=' ') -> str | None:
  """
  Функция преобразования datetime в строку с заданным разделителем
  :param value: datetime
  :return:
  """
  try:
    if value is None:
      return None
    else:
      return f'{separator}'.join([value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")])
  except:
    return None


def tuple_date_to_str(value: tuple) -> str:
  str = ''
  for item in value:
    str += '{0:s} '.format(item)
  return str


def dump_date_to_str(value) -> str | None:
  """
  Функция преобразования date в строку
  :param value: datetime
  :return:
  """
  try:
    if value is None:
      return None
    else:
      return value.strftime("%Y-%m-%d")
  except:
    return None


def convert_datetime_delete_to_str(recordset: Any) -> dict:
  """
  Функция конвертации datetime в строку, возвращает словарь с данными
  :param recordset: словарь записи таблицы Пользователей
  :return: словарь где datetime сконвертированно в строку
  """
  answer = recordset._asdict()
  answer.__setitem__('date_delete', dump_datetime_to_str(answer.get('date_delete')))
  return answer


def convert_datetime_to_str(recordset: Any) -> dict:
  """
  Функция конвертации datetime в строку, возвращает словарь с данными
  :param recordset: словарь записи таблицы Пользователей
  :return: словарь где datetime сконвертированно в строку
  """
  answer = recordset._asdict()
  answer.__setitem__('create_on', dump_datetime_to_str(answer.get('create_on')))
  answer.__setitem__('confirmed_on', dump_datetime_to_str(answer.get('confirmed_on')))
  return answer

def validate_date(value: str) -> datetime:
  """
  Функция проверки строки представляющей дату время и переводящей ее в datetime
  :param value: значение даты времени в виде строки
  :return:
  """
  try:
    if value is None:
      return datetime.utcnow()
    elif len(value) < DATETIME_MIN_LENGHT:
      return datetime.utcnow()
    else:
      value = value.replace('/', '.')
      value = value.replace('-', '.')
      if len(value) > 17:
        datetime_object = datetime.strptime(value, DATETIME_TEMPLATE)
      else:
        datetime_object = datetime.strptime(value, DATE_TEMPLATE)
      return datetime_object
  except:
    return datetime.utcnow()


def get_timedelta_to_days(start_date: datetime, end_date: datetime) -> int:
  """
  Функция рассчитывает кол-во дней между датами
  :param start_date:
  :param end_date:
  :return:
  """
  try:
    start_date = datetime(start_date.year, start_date.month, start_date.day)
    end_date = datetime(end_date.year, end_date.month, end_date.day)
    delta_time = end_date - start_date
    return delta_time.days
  except:
    return 0


def get_tomorrow(days: int = 1) -> datetime:
  '''
  Функция возвращает предыдущую дату на указанное кол-во дней, по умолчанию вчерашнюю
  :return:
  '''
  today = datetime.now()
  tomorrow = today + timedelta(days=days)
  return tomorrow
