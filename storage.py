"""Хранилище данных."""

import configparser
import logging
from pathlib import Path
from time import sleep

import redis


def config():
    """Получение данных из файла настроек хранилища"""
    parser = configparser.ConfigParser()
    config_file = str(Path(__file__).parent.joinpath('config.ini'))
    parser.read(config_file)
    parser_data = parser['storage']
    host = parser_data.get('HOST')
    port = int(parser_data.get('PORT'))
    timeout = int(parser_data.get('TIMEOUT'))
    return host, port, timeout


def retry(count=3, interval=1):
    """Подключение к базе данных."""
    def my_decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.info('Соединение с БД разорвано, попытка: %s', attempt)
                    attempt += 1
                    if attempt > count:
                        raise e
                    sleep(interval)
        return wrapper
    return my_decorator


HOST, PORT, SOCKET_TIMEOUT = config()


class Storage:
    """Хранилище данных Redis."""
    def __init__(self, host=HOST, port=PORT, socket_timeout=SOCKET_TIMEOUT):
        self._r = redis.Redis(host=host, port=port, socket_timeout=socket_timeout, decode_responses=True)

    def ping(self):
        """Пинг."""
        return self._r.ping()

    @retry()
    def get(self, key):
        """Получение значения из БД."""
        return self._r.get(key)

    @retry()
    def set(self, name, value, ex=None):
        """Запись значения в БД."""
        return self._r.set(name, value, ex)

    def cache_get(self, key):
        """Получение значения из кэш."""
        try:
            logging.info('Получение значения из кэш')
            return self._r.get(key)
        except Exception as e:
            logging.info(e)
            return None

    def cache_set(self, name, value, ex=None):
        """Запись значения в кэш."""
        try:
            logging.info('Запись значения в кэш')
            return self._r.set(name, value, ex)
        except Exception as e:
            logging.info(e)

    def create_interests(self):
        """Создание хобби в БД."""
        interests = [
            'cars',
            'pets',
            'travel',
            'hi-tech',
            'sport',
            'music',
            'books',
            'tv',
            'cinema',
            'geek',
            'otus',
        ]
        for number, interest in enumerate(interests, 1):
            self.set(f'i:{number}', interest)

    def disconnect(self):
        """Переподключение к БД."""
        self._r.connection_pool.disconnect()
