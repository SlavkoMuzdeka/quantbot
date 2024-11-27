from brokerage.oanda.TradeClient import TradeClient
from brokerage.oanda.ServiceClient import ServiceClient


class Oanda:
    def __init__(self, auth_config=""):
        self.trade_client = TradeClient(auth_config=auth_config)
        self.service_client = ServiceClient()

    def get_trade_client(self):
        return self.trade_client

    def get_service_client(self):
        return self.service_client
