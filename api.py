"""Api."""

import datetime
import hashlib
import json
import logging
import uuid
from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)
from argparse import ArgumentParser

from constants import (
    ADMIN_SALT,
    BAD_REQUEST,
    ERRORS,
    FORBIDDEN,
    INTERNAL_ERROR,
    INVALID_REQUEST,
    NOT_FOUND,
    OK,
    SALT,
)
from requests import (
    ClientsInterestsRequest,
    MethodRequest,
    OnlineScoreRequest,
)
from scoring import (
    get_interests,
    get_score,
)


def check_auth(request):
    """Проверка авторизации."""
    logging.info(f'Попытка авторизации как "{request.login}"')
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        logging.info('Успешная авторизация')
        return True
    logging.error(
        f'Неудачная авторизация, ожидался "{digest}",\n но получен "{request.token}"')
    return False


def authorization(func):
    """Авторизация."""
    def wrapper(request, ctx, store):
        response, code = ERRORS.get(FORBIDDEN), FORBIDDEN
        if check_auth(request):
            response, code = func(request, ctx, store)
        return response, code
    return wrapper


def method_handler(request, ctx, store):
    """Обработка метода."""
    try:
        req = MethodRequest()
        req.validate(request.get('body'))
        logging.info(f'Метод запроса: "{req.method}"')
        if req.method == 'online_score':
            response, code = online_score_handler(req, ctx, store)
        elif req.method == 'clients_interests':
            response, code = clients_interests_handler(req, ctx, store)
        else:
            logging.error('Неизвестный метод')
            response, code = ERRORS.get(INVALID_REQUEST), INVALID_REQUEST
        return response, code
    except ValueError:
        return ERRORS.get(INVALID_REQUEST), INVALID_REQUEST


@authorization
def online_score_handler(req, ctx, store):
    """Обработка метода подсчета."""
    arguments = req.arguments
    online_score = OnlineScoreRequest()
    online_score.validate(arguments)
    ctx['has'] = [key for key, val in arguments.items() if val is not None]
    if req.is_admin:
        score = int(ADMIN_SALT)
    else:
        score = get_score(
            store, online_score.phone, online_score.email,
            online_score.birthday,
            online_score.gender, online_score.first_name,
            online_score.last_name,
        )
    response = {'score': score}
    logging.info(f'Score: {score}')
    return response, OK


@authorization
def clients_interests_handler(req, ctx, store):
    """Обработка метода хобби клиентов."""
    clients_interests = ClientsInterestsRequest()
    clients_interests.validate(req.arguments)
    ctx['nclients'] = len(clients_interests.client_ids)
    interests = {_id: get_interests(store, _id) for _id in
                 clients_interests.client_ids}
    logging.info(f'Client interest: {interests}')
    return interests, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    """HTTP-Сервер."""

    router = {
        "method": method_handler
    }
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        logging.info(f'Новый контекст запроса: {context}')
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
            logging.info(f'Получен запрос: {request}')
        except Exception as e:
            code = BAD_REQUEST
            logging.error(e)

        if request:
            path = self.path.strip("/")
            if path in self.router:
                logging.info(f'Путь запроса: {path}')
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Ошибка: %s" % e)
                    code = INTERNAL_ERROR
            else:
                logging.error(f'{path} не верный путь запроса')
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    """Запуск сервера."""
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Старт сервера на %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
