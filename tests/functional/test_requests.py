"""Func tests."""

import datetime
import hashlib
import json
from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread

import pytest

import constants
from api import MainHTTPHandler

HOST = "localhost"
PORT = 8080


@pytest.fixture(scope='session', autouse=True)
def start_server():
    """Запуск сервера."""
    server = HTTPServer((HOST, PORT), MainHTTPHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    yield
    server.shutdown()
    thread.join()


@pytest.fixture(scope='session')
def client_connection():
    """Соединение с сервером."""
    connection = HTTPConnection(HOST, PORT)
    yield connection
    connection.close()


def create_request(client_connection, request):
    """Создание POST запроса."""
    client_connection.request('POST', '/method/', json.dumps(request))
    req = client_connection.getresponse()
    return json.load(req)


def set_valid_auth(request):
    """Установка валидной авторизации."""
    if request.get('login') == constants.ADMIN_LOGIN:
        request['token'] = (
            hashlib.sha512(
                (''.join((datetime.datetime.now().strftime("%Y%m%d%H"), constants.ADMIN_SALT))).encode('utf-8')
            ).hexdigest()
        )
    else:
        msg = request.get('account', '') + request.get('login', '') + constants.SALT
        request['token'] = hashlib.sha512(msg.encode('utf-8')).hexdigest()
    return request


class TestRequests:
    """Тестирование запросов."""

    @pytest.mark.parametrize(
        'req',
        [
            {
                'account': 'c3po',
                'login': 'c3po_login',
                'method': 'online_score',
                'token': 'aeaed', 'arguments': {'phone': '79999999999'},
            },
            {
                'account': 'c3po',
                'login': 'c3po_login',
                'method': 'online_score',
                'token': '',
                'arguments': {'phone': '79999999999'},
            },
            {'account': 'c3po', 'login': 'admin', 'method': 'online_score', 'token': '21212', 'arguments': {}},
        ],
    )
    def test_bad_auth(self, req, client_connection):
        """Неправильная (неудачная) авторизация."""
        response = create_request(client_connection, req)
        assert response.get('code') == constants.FORBIDDEN

    @pytest.mark.parametrize(
        'req', [
            {'account': 'c3po', 'login': 'c3po_login', 'method': 'offline_score'},
            {'account': 'c3po', 'login': 'c3po_login', 'arguments': {'phone': '79999999999'}},
            {'account': 'c3po', 'method': 'offline_score', 'arguments': {}},
        ],
    )
    def test_invalid_method_request(self, req, client_connection):
        """Некорректный метод запроса."""
        response = create_request(client_connection, req)
        assert response.get('code') == constants.INVALID_REQUEST

    @pytest.mark.parametrize(
        'args', [
            {},
            {'phone': '79999999999'},
            {'phone': '89999999999', 'email': 'grun_gespenst@tut.by'},
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by'},
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by', 'gender': 4},
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by', 'gender': '1'},
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by', 'gender': 1, 'birthday': '20.09.1610'},
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by', 'gender': 1, 'birthday': 'r2d2'},
            {
                'phone': '79999999999',
                'email': 'grun_gespenst@tut.by',
                'gender': 1,
                'birthday': '26.05.1982',
                'first_name': [],
            },
            {
                'phone': '79999999999',
                'email': 'grun_gespenst@tut.by',
                'gender': 1,
                'birthday': '26.05.1982',
                'first_name': "vladimir",
                "last_name": 2,
            },
            {'phone': '79999999999', 'birthday': '26.05.1982', 'first_name': 'vladimir'},
            {'email': 'grun_gespenst@tut.by', 'gender': 2, 'last_name': 2},
        ],
    )
    def test_invalid_score_request(self, args, client_connection):
        """Некорректный запрос подсчета баллов."""
        request = {'account': 'c3po', 'login': 'c3po_login', 'method': 'online_score', 'arguments': args}
        response = create_request(client_connection, request)
        assert response.get('code') == constants.INVALID_REQUEST

    def test_valid_score_admin_request(self, client_connection):
        """Валидный запрос подсчета баллов под пользователем Админ."""
        arguments = {'phone': '79999999999', 'email': 'grun_gespenst@tut.by'}
        request = {'account': 'c3po', 'login': 'admin', 'method': 'online_score', 'arguments': arguments}
        response = create_request(client_connection, set_valid_auth(request))
        assert response.get('code') == constants.OK
        assert response.get('response').get('score') == 42

    @pytest.mark.parametrize(
        'args', [
            {},
            {'date': '20.07.2017'},
            {'client_ids': [], 'date': '09.08.2020'},
            {'client_ids': {1: 2}, 'date': '09.08.2020'},
            {'client_ids': ['1', '2'], 'date': '09.08.2020'},
            {'client_ids': [1, 2], 'date': 'date'},
        ],
    )
    def test_invalid_interests_request(self, args, client_connection):
        """Некорректный запрос хобби клиентов."""
        request = {'account': 'c3po', 'login': 'c3po_login', 'method': 'clients_interests', 'arguments': args}
        response = create_request(client_connection, set_valid_auth(request))
        assert response.get('code') == constants.INVALID_REQUEST

    @pytest.mark.parametrize(
        "args", [
            {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
            {"client_ids": [1, 2], "date": "19.07.2017"},
            {"client_ids": [0]},
        ],
    )
    def test_valid_interests_request(self, args, client_connection):
        """Корректный запрос хобби клиентов."""
        request = {'account': 'c3po', 'login': 'c3po_login', 'method': 'clients_interests', 'arguments': args}
        response = create_request(client_connection, set_valid_auth(request))
        assert response.get('code') == constants.OK
        assert len(args['client_ids']) == len(response['response'])

    @pytest.mark.parametrize(
        "args", [
            {'phone': '79999999999', 'email': 'grun_gespenst@tut.by'},
            {'phone': 79999999999, 'email': 'grun_gespenst@tut.by'},
            {'gender': 0, 'birthday': '26.05.1982', 'first_name': 'Kastus', 'last_name': 'Kalinouski'},
            {'gender': 1, 'birthday': '26.05.1982'},
            {'gender': 2, 'birthday': '26.05.1982'},
            {'first_name': 'a', 'last_name': 'b'},
            {
                'phone': '79175002040',
                'email': 'grun_gespenst@tut.by',
                'gender': 1,
                'birthday': '01.01.2000',
                'first_name': 'Kastus',
                'last_name': 'Kalinouski'},
        ],
    )
    def test_valid_score_request(self, args, client_connection):
        """Корректный запрос подсчета баллов."""
        request = {'account': 'c3po', 'login': 'c3po_login', 'method': 'online_score', 'arguments': args}
        response = create_request(client_connection, set_valid_auth(request))
        assert response.get("code") == constants.OK
