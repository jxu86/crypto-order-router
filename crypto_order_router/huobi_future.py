from huobi_future import RequestClient
from huobi_future.model import *


class OrderRouter(object):
    def __init__(self, apikey, secretkey, password):
        self._api = RequestClient(api_key=apikey, secret_key=secretkey)
        self.account_type = AccountType.FUTURE


    def get_account_info(self):
        account = self._api.get_account_balance()

        balance_list = []
        for balance in account.balances:
            balance_list.append({
                'currency': balance.currency,
                'balance': balance.balance,
                'frozen': balance.frozen,
                'position': balance.position,
                'available': balance.available
            })

        return balance_list


    