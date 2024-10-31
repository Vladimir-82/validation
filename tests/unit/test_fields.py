"""Unit tests."""

import datetime

import pytest

from validation import (
    EmailField,
    ClientIDsField,
    GenderField,
    BirthDayField,
    PhoneField,
)


class TestEmailField:
    """Unit tests для EmailField."""

    @pytest.mark.parametrize('value', ('test@tut.by', 'test2@yuy.ua', 'test3@@yuy.us'), ids=['by', 'ua', 'us'])
    def test_valid_email(self, value):
        """Валидный email."""
        assert EmailField().validate(value)

    @pytest.mark.parametrize('value', ('test1.tut.by', 'test2%yuy.ua', [1, 2]), ids=['by', 'ua', 'list'])
    @pytest.mark.xfail
    def test_invalid_email(self, value):
        """Невалидный email."""
        with pytest.raises(ValueError):
            assert EmailField().validate(value)


class TestClientIdsField:
    """Unit tests для ClientIds."""

    @pytest.mark.parametrize('value', ([1, 2, 3], [99], [5656565, 88888]), ids=['1_2_3', '99', 'big_ids'])
    def test_valid_client_ids(self, value):
        """Валидные идентификаторы."""
        assert ClientIDsField().validate(value)

    @pytest.mark.parametrize('value', (['r2d2', 33], [], [{'set'}]), ids=['string', 'empty', 'set'])
    @pytest.mark.xfail
    def test_invalid_client_ids(self, value):
        """Невалидные идентификаторы."""
        with pytest.raises(ValueError):
            assert ClientIDsField().validate(value)


class TestGenderFiled:
    """Unit tests для GenderFiled."""

    @pytest.mark.parametrize('value', (0, 1, 2), ids=['0', '1', '2'])
    def test_valid_gender(self, value):
        """Валидный возраст."""
        assert GenderField().validate(value)

    @pytest.mark.parametrize('value', (99, -1, 'c3po'), ids=['99', 'negatively', 'string'])
    @pytest.mark.xfail
    def test_invalid_gender(self, value):
        """Невалидный возраст."""
        with pytest.raises(ValueError):
            assert GenderField().validate(value)


class TestBirthdayField:
    """Unit tests для BirthdayField."""

    @pytest.mark.parametrize('value', ('26.05.1982', datetime.date.today().strftime('%d.%m.%Y')), ids=['date', 'today'])
    def test_valid_birthday(self, value):
        """Валидный день рождения."""
        assert BirthDayField().validate(value)

    @pytest.mark.parametrize(
        'value', (3, '26.13.1982', 'a', '1990.12.01'), ids=['int', 'wrong_date', 'string', 'wrong_format_date']
    )
    @pytest.mark.xfail
    def test_invalid_birthday(self, value):
        """Невалидный день рождения."""
        with pytest.raises(ValueError):
            assert BirthDayField().validate(value)


class TestPhoneField:
    """Unit tests для PhoneField."""

    @pytest.mark.parametrize('value', ('71234567891', 71234567891), ids=['string', 'int'])
    def test_valid_phone(self, value):
        """Валидный номер телефона."""
        assert PhoneField().validate(value)

    @pytest.mark.parametrize(
        'value', ('765', 'c3po', '80295603750', '0295603750a', 7123456789123456),
        ids=['to_small', 'letters', 'wrong_starts', 'letters_in_num', 'to_big'],
    )
    @pytest.mark.xfail
    def test_invalid_phone(self, value):
        """Невалидный номер телефона."""
        with pytest.raises(ValueError):
            assert PhoneField().validate(value)
