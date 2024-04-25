import os
import threading

import flask
from flask import Flask

from keys.key_pool import KeyPool
from keys.key_store import KeyStore
from network.broadcaster import Broadcaster
from network.scanner import Scanner
from router.external import External
from router.internal import Internal
from server import tls
from server.request_handler import PeerCertWSGIRequestHandler


class App:
    def __init__(self, app: Flask):
        self.app = app

        self.kme_list = []
        self.kme_lock = threading.Lock()
        self.scanner = Scanner(self.kme_list, self.kme_lock)

        self.gen_lock = threading.Lock()
        self.key_pool = KeyPool(self.gen_lock)

        self.broadcaster = Broadcaster()
        self.key_store = KeyStore(self.key_pool, self.broadcaster)

        self.external_routes = External(self.scanner, self.key_store)
        self.internal_routes = Internal(self.scanner, self.key_store)

    def start(self):
        scanner_thread = threading.Thread(target=self.scanner.start)
        scanner_thread.start()

        key_pool_thread = threading.Thread(target=self.key_pool.start)
        key_pool_thread.start()

        self.__run()

    def stop(self):
        self.scanner.stop.set()
        self.key_pool.stop.set()

    def before_request(self):
        self.kme_lock.acquire(blocking=True)
        self.gen_lock.acquire(blocking=True)

    def after_request(self, response: flask.Response):
        self.kme_lock.release()
        self.gen_lock.release()

        return response

    def __run(self):
        self.app.run(
            host=os.getenv('HOST'),
            port=os.getenv('PORT'),
            ssl_context=tls.create_ssl_context(),
            request_handler=PeerCertWSGIRequestHandler
        )
