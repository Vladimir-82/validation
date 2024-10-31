"""Integration tests."""

import uuid
from time import sleep

from storage import Storage

STORAGE = Storage()


class TestStorage:
    """Integration tests."""

    def test_get_set(self):
        """Test get и set методов БД."""
        name, value = 'name', 'value'
        assert STORAGE.set(name, value)
        assert STORAGE.get(name) == value

    def test_cache_set(self):
        """Test записи в кэш."""
        name, value = 'name', 'value'
        assert STORAGE.set(name, value, ex=2)
        assert STORAGE.get(name) == value
        sleep(3)
        assert STORAGE.get(name) is None

    def test_cache_get(self):
        """Test записи в кэш и переподключении к БД."""
        name, value = uuid.uuid4().int, uuid.uuid4().int
        STORAGE.set(name, value)
        STORAGE.disconnect()
        assert STORAGE.cache_get(uuid.uuid4().int) is None

    def test_reconnect(self):
        """Test проверки работы БД и переподключении к БД."""
        name, value = 'name', 'value'
        assert STORAGE.ping()
        STORAGE.disconnect()
        assert STORAGE.set(name, value)
        assert STORAGE.get(name) == value
