import sys

from colorama import Fore, Style
from colorama import init as colorama_init

from config import BaseConfig

colorama_init()

import psycopg2
from psycopg2.extras import NamedTupleCursor

print(
    Fore.GREEN + Style.BRIGHT + 'PostgreSQL connection string: ' + Style.RESET_ALL + Fore.BLUE + Style.BRIGHT + BaseConfig.DB_URI + Style.RESET_ALL)


class DbPsycopg:
    def __init__(self):
        self.conn = psycopg2.connect(
            user=BaseConfig.DB_USER,
            password=BaseConfig.DB_PASSWORD,
            host=BaseConfig.DB_HOST,
            port=BaseConfig.DB_PORT,
            database=BaseConfig.DB_NAME
        )

        self.conn.autocommit = True

    def fetch_one(self, query, arg=None, factory=None, clean=None):
        """ Получает только одно ЕДИНСТВЕННОЕ значение (не ряд!) из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dic (возвращает словарь - ключ/значение) или list (возвращает list)
        :param clean: С параметром вернет только значение. Без параметра вернет значение в кортеже.
        """
        try:
            cur = self.__connection(factory)
            self.__execute(cur, query, arg)
            return self.__fetch(cur, clean)

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def fetch_all(self, query, arg=None, factory=None):
        """ Получает множетсвенные данные из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dic (возвращает словарь - ключ/значение) или list (возвращает list)
        """
        try:
            cur = self.__connection(factory)
            self.__execute(cur, query, arg)
            return cur.fetchall()

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def query_update(self, query, arg, message=None):
        """ Обновляет данные в таблице и возвращает сообщение об успешной операции """
        try:
            cur = self.conn.cursor()
            cur.execute(query, arg)
            return message

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def close(self):
        cur = self.conn.cursor()
        cur.close()
        self.conn.close()

    def __connection(self, factory=None):
        # Dic - возвращает словарь - ключ/значение
        if factory == 'dic':
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # List - возвращает list (хотя и называется DictCursor)
        elif factory == 'list':
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Tuple
        else:
            cur = self.conn.cursor()

        return cur

    @staticmethod
    def __execute(cur, query, arg=None):
        # Метод 'execute' всегда возвращает None
        if arg:
            cur.execute(query, arg)
        else:
            cur.execute(query)

    @staticmethod
    def __fetch(cur, clean):
        # Если запрос был выполнен успешно, получим данные с помощью 'fetchone'
        if clean == 'no':
            # Вернет:
            #   Название:
            #       ('Royal Caribbean Cruises',)
            #   Дата:
            #       (datetime.datetime(2020, 6, 2, 13, 36, 35, 61052, tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None)),)
            fetch = cur.fetchone()
        else:
            # Вернет:
            #   Название:
            #       Royal Caribbean Cruises
            #   Дата:
            #       (da2020-06-02 13:36:35.061052+00:00
            fetch = cur.fetchone()[0]
        return fetch

    @staticmethod
    def __error(error):
        # В том числе, если в БД данных нет, будет ошибка на этапе fetchone
        print('Данных в бд нет или ошибка: {}'.format(error))
        return None


if __name__ == "__main__":
    try:
        if sys.argv[1]:
            mode = sys.argv[1]
        if sys.argv[2]:
            arg2 = sys.argv[2]
        # if sys.argv[3]:
        # arg3 = sys.argv[3]
    except:
        print('Необходимо использовать параметры:\nНапример:')
        # print('python pgs.py export table to_file.csv')
        # print('python pgs.py import from_file.csv')
        print('python pgs.py exe "select * from refs.options"')
        sys.exit(0)
    if mode == 'exe':
        query = arg2
    if mode == 'inport':  # todo
        # q="COPY (SELECT * FROM refs.options where (1=1)) TO 'd:\_proj\_rg\options2.csv' CSV HEADER;"
        pass
    if mode == 'export':  # todo
        # q="COPY employees(id,firstname,lastname,email) FROM '/tmp/sample.csv' DELIMITER ',' CSV HEADER;"
        pass
    dbps = DbPsycopg()
    # query = "SELECT version();"
    print(Fore.YELLOW + query + Style.RESET_ALL)
    result = dbps.fetch_all(query)
    print(result)
