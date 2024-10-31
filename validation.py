"""Валидация данных."""

import datetime

UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: 'unknown',
    MALE: 'male',
    FEMALE: 'female',
}


class Field:
    """Базовый класс."""

    _type = None

    def __init__(self, required=False, nullable=False):
        """Метод - init."""
        self.required = required
        self.nullable = nullable
        self._name = None

    def __get__(self, instance, owner):
        """Получение атрибута."""
        return instance.__dict__[self._name]

    def __set_name__(self, owner, name):
        """Имя атрибута."""
        self._name = '_' + name

    def __set__(self, owner, value):
        """Изменение атрибута."""
        if value is None and (self.required or not self.nullable):
            raise ValueError(f'{self.__class__.__name__} обязательный')
        if (value is None or value == '') and self.nullable:
            owner.__dict__[self._name] = None
        else:
            if isinstance(value, self._type):
                self.validate(value)
                owner.__dict__[self._name] = value
            else:
                raise ValueError(
                    f'{self.__class__.__name__} должен быть {self._type}, но получен {type(value).__name__}')

    def validate(self, value):
        """Валидация."""
        pass


class CharField(Field):
    """Строковый тип данных."""

    _type = str


class ArgumentsField(Field):
    """Тип данных - словарь."""

    _type = dict


class EmailField(CharField):
    """Тип данных - email."""

    def validate(self, value):
        """Валидация."""
        if value and '@' not in value:
            raise ValueError('Адрес должен содержать "@')
        return True


class PhoneField(Field):
    """Тип данных - телефон."""

    _type = (int, str)

    def validate(self, value):
        """Валидация."""
        value = str(value)
        if not value:
            pass
        elif len(value) != 11:
            raise ValueError('Телефон должен состоять из 11 цифр')
        elif not value.isdigit():
            raise ValueError('Телефон должен состоять только из цифр')
        elif not value.startswith('7'):
            raise ValueError('Телефон должен начинаться с 7')
        return True


class DateField(CharField):
    """Тип данных - дата."""

    def validate(self, value):
        """Валидация."""
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError('Дата не корректна')


class BirthDayField(DateField):
    """Тип данных - дата рождения."""

    def validate(self, value):
        """Валидация."""
        super().validate(value)
        value = str(value)
        birthday_year = datetime.datetime.strptime(value, '%d.%m.%Y').year
        year_today = datetime.date.today().year
        if year_today - birthday_year > 70:
            raise ValueError('Прошло более 70 лет со дня рождения')
        return True


class GenderField(Field):
    """Тип данных - пол."""

    _type = int

    def validate(self, value):
        """Валидация."""
        if value not in GENDERS:
            raise ValueError('Неизвестный пол')
        return True


class ClientIDsField(Field):
    """Тип данных - список id."""

    _type = list

    def validate(self, id_values):
        """Валидация."""
        all_is_int = all([type(id_value) is int for id_value in id_values]) if id_values else False
        if not all_is_int:
            raise ValueError('Перечень клиентов должен содержать только цифры (id)')
        return True
