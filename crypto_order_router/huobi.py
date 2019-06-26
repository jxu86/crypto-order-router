# -*- coding: utf-8 -*-

import time
import datetime
import math
from huobi import RequestClient
from huobi.model import *
import pandas as pd


class ORDER_TYPE(OrderType):
    pass


class OrderRouter(object):
    def __init__(self, apikey, secretkey, password):
        self._api = RequestClient(api_key=apikey, secret_key=secretkey)
        self.account_type = AccountType.SPOT

    def _format_instrument_id(self, instrument_id):
        return instrument_id.lower().replace('-', '')

    def _decode_type(self, order_type):
        if not order_type:
            return None, None
        tmp = order_type.split('-')
        side = tmp[0]
        o_type = tmp[1]
        if side not in ['buy', 'sell']:
            side = None

        if o_type not in ['limit', 'market', 'ioc']:
            o_type = None

        return side, o_type

    def _decode_state(self, state):
        if state == 'submitted':
            return 'open'

        return state

    def _timestamp_to_datetime(self, timestamp):
        return datetime.datetime.fromtimestamp((timestamp + 28800000) / 1000)

    def _format_order(self, instrument_id, order_info):
        def fill_obj(o):
            side, o_type = self._decode_type(o.order_type)
            return {
                'instrument_id':
                instrument_id,
                'order_id':
                str(o.order_id),
                'client_oid':
                '',
                'price':
                o.price,
                'size':
                o.amount,
                'timestamp':
                o.created_timestamp,
                'finished_timestamp':
                o.finished_timestamp,
                'finished_datetime':
                self._timestamp_to_datetime(o.finished_timestamp),
                'canceled_timestamp':
                o.canceled_timestamp,
                'datetime':
                self._timestamp_to_datetime(o.created_timestamp),
                'filled_size':
                o.filled_amount,
                'filled_notional':
                o.filled_cash_amount,
                'side':
                side,
                'type':
                o_type,
                'state':
                o.state,
                'status':
                self._decode_state(o.state),
                'created_at':
                datetime.datetime.now(),
                'updated_at':
                datetime.datetime.now()
            }

        if isinstance(order_info, list):
            ret = []
            for o in order_info:
                ret.append(fill_obj(o))
        else:
            ret = fill_obj(order_info)

        return ret

    def check_position(self, symbol):
        psss

    def submit_spot_order(self,
                          client_oid,
                          type,
                          side,
                          instrument_id,
                          price,
                          size,
                          notional,
                          order_type='0',
                          timeout=20,
                          wait_flag=False):

        instrument_id = self._format_instrument_id(instrument_id)
        order_type = '{}-{}'.format(param['side'], param['type'])
        order_id = self._api.create_order(instrument_id, self.account_type,
                                          order_type, size, price)
        return {'order_id': order_id}

    # take orders
    # 市价单
    # params = [
    #   {"client_oid":"20180728","instrument_id":"btc-usdt","side":"sell","type":"market"," size ":"0.001"," notional ":"10001","margin_trading ":"1"},
    #   {"client_oid":"20180728","instrument_id":"btc-usdt","side":"sell","type":"limit"," size ":"0.001","notional":"10002","margin_trading ":"1"}
    # ]

    # 限价单
    # params = [
    #   {"client_oid":"20180728","instrument_id":"btc-usdt","side":"sell","type":"limit","size":"0.001","price":"10001","margin_trading ":"1"},
    #   {"client_oid":"20180728","instrument_id":"btc-usdt","side":"sell","type":"limit","size":"0.001","price":"10002","margin_trading ":"1"}
    # ]
    def submit_orders(self, params):
        ret = []
        for param in params:
            instrument_id = self._format_instrument_id(param['instrument_id'])
            order_type = '{}-{}'.format(param['side'], param['type'])
            order_id = self._api.create_order(instrument_id, self.account_type,
                                              order_type, param['size'],
                                              param['price'])
            order_id = str(order_id)
            print('submit order id: {}, order_type: {}, price: {}'.format(
                order_id, order_type, param['price']))
            ret.append({
                'order_id': order_id,
                'side': param['side'],
                'price': param['price']
            })
            time.sleep(0.01)

        return ret

    def get_order_info(self, order_id, instrument_id, client_oid=''):
        order_info = self._api.get_order(
            self._format_instrument_id(instrument_id), order_id)

        return self._format_order(instrument_id, order_info)

    def cancel_order(self, order_id, instrument_id):
        return self._api.cancel_order(
            self._format_instrument_id(instrument_id), order_id)

    # revoke orders

    # params example:
    # [
    #   {"instrument_id":"btc-usdt","order_ids":[1600593327162368,1600593327162369]},
    #   {"instrument_id":"ltc-usdt","order_ids":[243464,234465]}
    # ]
    def cancel_orders(self, params):
        ret = []
        for param in params:
            instrument_id = self._format_instrument_id(param['instrument_id'])
            ret.append(
                self._api.cancel_orders(instrument_id, param['order_ids']))
            time.sleep(0.01)

        return ret

    def get_orders_pending(self, instrument_id):
        ret = []
        open_orders = self._api.get_open_orders(
            self._format_instrument_id(instrument_id),
            self.account_type,
            size=100)
        return self._format_order(instrument_id, open_orders)

    def get_kline(self, instrument_id, start, end, granularity):
        pass

    def get_ticker(self, instrument_id):
        last_trade = self._api.get_last_trade(
            self._format_instrument_id(instrument_id))

        return {'last': last_trade.price}

    def get_coin_info(self, instrument_id='all'):
        # TODO 把sdk方法get_exchange_info的symobl和currency分离出来

        exchange_info = self._api.get_exchange_info()
        symbol_list = exchange_info.symbol_list

        for sl in symbol_list:
            if sl.symbol == self._format_instrument_id(instrument_id):
                return {
                    'instrument_id': instrument_id,
                    'base_currency': sl.base_currency,
                    'quote_currency': sl.quote_currency,
                    'tick_size': sl.price_precision,
                    'size_increment': sl.amount_precision
                }
        return None

    def get_account_info(self):
        account_balances = self._api.get_account_balance_by_account_type(
            self.account_type)
        details_obj = {}
        for b in account_balances.balances:
            if b.balance:
                if b.currency not in details_obj:
                    if b.balance_type == BalanceType.TRADE:
                        details_obj[b.currency] = {
                            'currency': b.currency.upper(),
                            'frozen': 0,
                            'balance': b.balance,
                            'available': b.balance
                        }
                    elif b.balance_type == BalanceType.FROZEN:
                        details_obj[b.currency] = {
                            'currency': b.currency.upper(),
                            'frozen': b.balance,
                            'balance': b.balance,
                            'available': 0
                        }
                else:
                    if b.balance_type == BalanceType.TRADE:
                        details_obj[b.currency]['available'] += b.balance
                        details_obj[b.currency]['balance'] += b.balance

                    elif b.balance_type == BalanceType.FROZEN:
                        details_obj[b.currency]['frozen'] += b.balance
                        details_obj[b.currency]['balance'] += b.balance

        return list(details_obj.values())

    def get_coin_account_info(self, symbol):
        balances = self._api.get_account_balance_by_account_type(
            self.account_type)
        ret = {'currency': symbol, 'frozen': 0, 'balance': 0, 'available': 0}
        for b in balances.get_balance(symbol.lower()):
            if b.balance_type == BalanceType.TRADE:
                ret['balance'] += b.balance
                ret['available'] = b.balance
            elif b.balance_type == BalanceType.FROZEN:
                ret['balance'] += b.balance
                ret['frozen'] = b.balance

        return ret

    def get_coin_balance(self, symbol):
        return self.get_coin_account_info(symbol)['balance']

    def get_coin_available(self, symbol):
        return self.get_coin_account_info(symbol)['available']

    def get_oneday_orders(self, instrument_id, stime, state):
        if stime > datetime.datetime.now():
            return []

        start_date = stime.strftime('%Y-%m-%d')
        end_date = start_date  # (stime + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        orders = []
        start_id = None
        size = 100
        format_instrument_id = self._format_instrument_id(instrument_id)
        while True:
            order = self._api.get_historical_orders(
                format_instrument_id,
                state,
                start_date=start_date,
                end_date=end_date,
                start_id=start_id,
                size=size)
            format_orders = self._format_order(instrument_id, order)
            orders += format_orders
            # print('Fetched orders, pair: %s, total: %d', instrument_id, len(format_orders))
            if len(format_orders) < size:
                break
            else:
                start_id = min([o['order_id'] for o in format_orders])
            time.sleep(0.5)
        return orders

    def get_orders(self, instrument_id, stime, etime, state):
        date_list = pd.date_range(
            stime.replace(hour=0, minute=0, second=0, microsecond=0),
            etime.replace(hour=0, minute=0, second=0, microsecond=0))
        orders = []
        for d in date_list:
            orders += self.get_oneday_orders(instrument_id, d, state)

        return [
            o for o in orders
            if o['datetime'] >= stime and o['datetime'] < etime
        ]
