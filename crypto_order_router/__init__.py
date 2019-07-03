# -*- coding: utf-8 -*-
import importlib
__all__ = ['okex', 'huobi', 'huobi_future', 'constant']

class OrderRouter(object):
    def __init__(self, exchange, apikey, secretkey, passphrase):
        self.exchange, self.apikey, self.secretkey, self.passphrase = exchange, apikey, secretkey, passphrase
        print('exchange:{}'.format(self.exchange))
    def _load_module(self, module_name):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                'Exchange websocket module not found: {}'.format(
                    module_name))
        return module

    def get_exchange_order_router(self):
        module = self._load_module('crypto_order_router.{}'.format(self.exchange))
        print('import module:{}'.format(module))
        return module.OrderRouter(self.apikey, self.secretkey, self.passphrase)
