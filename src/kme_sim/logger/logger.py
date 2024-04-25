import os
from datetime import datetime


def __print(status: str, message: str) -> None:
    print(f'{status}: [{datetime.now()}] "{message}"')


def debug(message: str) -> None:
    if os.getenv('DEBUG'):
        __print('DEBG', message)


def info(message: str) -> None:
    __print('INFO', message)


def warn(message: str) -> None:
    __print('WARN', message)


def error(message: str) -> None:
    __print('ERRO', message)
