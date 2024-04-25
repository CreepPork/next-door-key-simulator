import os
from datetime import datetime


def __print(status: str, message: str, *args) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ({status}): "{message}"', *args)


def debug(message: str, *args) -> None:
    if os.getenv('DEBUG'):
        __print('DEBG', message, *args)


def info(message: str, *args) -> None:
    __print('INFO', message, *args)


def warn(message: str, *args) -> None:
    __print('WARN', message, *args)


def error(message: str, *args) -> None:
    __print('ERRO', message, *args)
