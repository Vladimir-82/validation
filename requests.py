"""Запросы."""

import logging

from constants import ADMIN_LOGIN
from validation import (
    ArgumentsField,
    BirthDayField,
    CharField,
    ClientIDsField,
    DateField,
    EmailField,
    Field,
    GenderField,
    PhoneField,
)


class ApiRequest:
    """Базовая модель валидации запроса."""

    def __init__(self):
        """Метод init."""
        self.fields = [field for field, value in self.__class__.__dict__.items() if isinstance(value, Field)]

    def validate(self, kwargs):
        """Валидация запроса."""
        logging.info(f'Доступные поля {self.__class__.__name__}: {self.fields}')
        logging.info(f'Полученные поля {self.__class__.__name__}: {list(kwargs.keys())}')

        errors = []
        for field in self.fields:
            value = kwargs[field] if field in kwargs else None
            try:
                setattr(self, field, value)
            except ValueError as e:
                errors.append(e)
                logging.error(e)
        if errors:
            raise ValueError('Ошибка валидации полей')


class ClientsInterestsRequest(ApiRequest):
    """Валидация запроса клиентов."""

    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(ApiRequest):
    """Валидация запроса подсчета баллов."""

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self, kwargs):
        """Валидация запроса."""
        super().validate(kwargs)
        validate_pairs = any(
            [self.phone and self.email, self.first_name and self.last_name, self.gender is not None and self.birthday]
        )
        if not validate_pairs:
            logging.error(
                'Ожидается по крайней мере одна пара из (first_name - last_name, email - phone, birthday - gender)')
            raise ValueError('Ошибка валидации полей')


class MethodRequest(ApiRequest):
    """Валидация метода запроса."""

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=True)

    @property
    def is_admin(self):
        """Авторизация админа."""
        return self.login == ADMIN_LOGIN
