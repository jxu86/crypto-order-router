# -*- coding: utf-8 -*-

import okex.spot_api as spot_api
import time
import datetime
import crypto_order_router.utils as utils
import math

class OrderRouter(object):
    def __init__(self, apikey, secretkey, password):
        self.last_pending_order_time = None
        self.last_pending_orders = None
        self.spot_api = spot_api.SpotAPI(apikey, secretkey, password, True)


    def check_position(self, symbol):
        return self.spot_api.get_coin_account_info(symbol)

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
        print('###submit_spot_order=>side==>', side, ' ==>', price)
        order_info = None
        try:
            order_info = self.spot_api.take_order(
                client_oid=client_oid,
                instrument_id=instrument_id,
                type=type,
                order_type=order_type,
                side=side,
                size=size,
                price=price)
            print('submit_spot_order=>order_info==>', order_info)
        except:
            print('#######submit_spot_order=>e==>')
            return None

        time.sleep(0.08)
        order_id = order_info['order_id']
        try:
            order = self.spot_api.get_order_info(
                instrument_id=instrument_id, order_id=order_id)
            print('spot order2==>', order)
        except:
            # self.add_order(instrument_id=instrument_id, price=price, t_price=0, size=size, side=side, order=order_info)
            print('spot read order info err')
            return order_info

        while wait_flag:
            time.sleep(0.2)
            try:
                order = self.spot_api.get_order_info(
                    instrument_id=instrument_id, order_id=order_id)
                if order['status'] == 'filled':  #部分成交 全部成交 撤单
                    return order
            except:
                print('spot read order info err')
        # self.add_order(instrument_id=instrument_id, price=price, t_price=0, size=size, side=side, order=order)

        return order

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
        n = 10  # 一次只能批量10个单
        new_params = [
            params[i * n:(i + 1) * n]
            for i in range(math.ceil(len(params) / n))
        ]
        orders_info = []
        for param in new_params:
            orders_info.append(self.spot_api.take_orders(param))
            time.sleep(0.04)
        return orders_info

    def get_order_info(self, order_id, instrument_id, client_oid=''):
        return self.spot_api.get_order_info(
            instrument_id=instrument_id,
            order_id=order_id,
            client_oid=client_oid)

    def cancel_order(self, order_id, instrument_id):
        ret = self.spot_api.revoke_order(order_id, instrument_id)
        return ret

    # revoke orders

    # params example:
    # [
    #   {"instrument_id":"btc-usdt","order_ids":[1600593327162368,1600593327162369]},
    #   {"instrument_id":"ltc-usdt","order_ids":[243464,234465]}
    # ]
    def cancel_orders(self, params):
        return self.spot_api.revoke_orders(params)

    def _format_order(self, order):

        def fill_obj(o):
            o['price'] = float(o['price'])
            o['filled_notional'] = float(o['filled_notional'])
            o['filled_size'] = float(o['filled_size'])
            o['size'] = float(o['size'])
            return o

        if isinstance(order, list):
            for o in order:
                o = fill_obj(o)
        else:
            order = fill_obj(fill_obj)

        return order

    def get_orders_pending(self, instrument_id):
        now_time = time.time()
        # 20次2s
        if self.last_pending_order_time and (now_time - self.last_pending_order_time < 0.1):
            return self.last_pending_orders
        else:
            open_orders = self.spot_api.get_orders_pending(
            froms='', to='', limit='100', instrument_id=instrument_id)
            self.last_pending_orders = list(open_orders[0])
            self.last_pending_order_time = time.time()

        return self.last_pending_orders

    def get_kline(self, instrument_id, start, end, granularity):
        klines = self.spot_api.get_kline(instrument_id, start, end,
                                         granularity)
        if klines and len(klines):
            fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            return [dict(zip(fields, r)) for r in klines]
        return None

    def get_ticker(self, instrument_id):
        return self.spot_api.get_specific_ticker(instrument_id)

    def get_coin_info(self, instrument_id):
        coin_info = self.spot_api.get_coin_info()
        info = [
            i for i in coin_info if i['instrument_id'] == instrument_id
        ]
        if info:
            ret = info[0]
            ret['tick_size'] = utils.get_float_precision(ret['tick_size'])
            ret['min_size'] = float(ret['min_size'])
            return ret
        else:
            return None
                
    def get_account_info(self):
        return self.spot_api.get_account_info()

    def get_coin_account_info(self, symbol):
        return self.spot_api.get_coin_account_info(symbol)
    
    def get_coin_balance(self, symbol):
        info = self.spot_api.get_coin_account_info(symbol)

        return float(info.get('balance', '0'))

    def get_coin_available(self, symbol):
        info = self.spot_api.get_coin_account_info(symbol)
        return float(info.get('available', '0'))

    def get_orders(self, symbol, stime, etime, state=''):
        froms = None
        order_list = []
        last_order = {}
        after = ''
        while True:
            if froms == None:
                orders = self.spot_api.get_orders_list(state, symbol)
            else:
                orders = self.spot_api.get_orders_list(state, symbol, froms=froms)
            order_position = orders[1]
            orders = list(orders[0])

            if len(orders) <= 0:
                break

            after = order_position['after']
            if len(order_list) and order_list[-1] == orders[0]:
                order_list = order_list + orders[1:]
            else:
                order_list = order_list + orders

            if stime == '' and etime == '':
                break
            # print('orders len=>', len(order_list))
            if utils.utcstr_to_datetime(order_list[-1]['timestamp']) <= stime:
                break

            # if to == order_list[-1]['order_id']:
            #     break
            froms = order_list[-1]['order_id']
            # print('froms ==>', froms)
            time.sleep(1)
        new_order_list = []
        for l in order_list:
            l['created_at'] = utils.utcstr_to_datetime(l['created_at'])
            l['datetime'] = utils.utcstr_to_datetime(l['timestamp'])
            l['filled_notional'] = float(l['filled_notional'])
            l['filled_size'] = float(l['filled_size'])
            if l['price']:
                l['price'] = float(l['price'])
            else:
                l['price'] = 0
            l['size'] = float(l['size'])
            if stime == '' and etime == '':
                new_order_list.append(l)
            elif l['datetime'] >= stime and l['datetime'] <= etime:
                new_order_list.append(l)
            l = str(l)
        return new_order_list
