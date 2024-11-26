import json
import datetime
import pandas as pd

import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments


class TradeClient:
    def __init__(self, auth_config):
        self.id = auth_config["oanda_account_id"]
        self.token = auth_config["oanda_token"]
        self.env = auth_config["oanda_env"]
        self.client = oandapyV20.API(access_token=self.token, environment=self.env)

    def get_account_details(self):
        try:
            return self.client.request(accounts.AccountDetails(accountID=self.id))[
                "account"
            ]
        except Exception as ex:
            print(f"An error occurs while getting account details - {ex}")
            raise

    def get_account_instruments(self):
        try:
            instruments_data = self.client.request(
                accounts.AccountInstruments(accountID=self.id, params={})
            )
            instruments = {}
            currencies, cfds, metals = [], [], []
            for inst in instruments_data:
                inst_name = inst["name"]
                inst_type = inst["type"]

                instruments[inst_name] = {"type": inst_type}
                if inst_type == "CFD":
                    cfds.append(inst_name)
                elif inst_type == "CURRENCY":
                    currencies.append(inst_name)
                elif inst_type == "METAL":
                    metals.append(inst_name)
                else:
                    print(f"Unknow type - {inst_type}")
                    break
            return instruments, currencies, cfds, metals
        except Exception as ex:
            print(f"An error occurs while getting account instrumets - {ex}")
            raise

    def get_account_summary(self):
        try:
            return self.client.request(accounts.AccountSummary(accountID=self.id))[
                "account"
            ]
        except Exception as ex:
            print(f"An error occurs while getting account summary - {ex}")
            raise

    def get_account_capital(self):
        try:
            return float(self.get_account_summary()["NAV"])
        except Exception as ex:
            print(f"An error occurs while getting account capital - {ex}")
            raise

    def get_account_positions(self):
        try:
            positions_data = self.get_account_details()["positions"]
            positions = {}
            for entry in positions_data:
                instrument = entry["instrument"]
                long_pos = int(entry["long"]["units"])
                short_pos = int(entry["short"]["units"])
                net_pos = long_pos + short_pos
                if net_pos != 0:
                    positions[instrument] = net_pos

            return positions
        except Exception as ex:
            print(f"An error occurs while getting account positions - {ex}")
            raise

    def get_account_trades(self):
        try:
            return self.get_account_details()["trades"]
        except Exception as ex:
            print(f"An error occurs while getting account trades - {ex}")
            raise

    def is_tradable(self, inst):
        try:
            params = {"instruments": inst}
            pricing_data = self.client.request(
                pricing.PricingInfo(accountID=self.id, params=params)
            )
            return pricing_data["prices"][0]["tradeable"]
        except Exception as ex:
            print(f"An error occurs while checking if instruments are tradable - {ex}")
            raise

    def get_endpoint(self, inst):
        pass

    def get_ohlcv(self, instrument, count, granularity):
        params = {"count": count, "granularity": granularity}
        candles = self.client.request(
            instruments.InstrumentsCandles(instrument=instrument, params=params)
        )
        ohlc_dict = candles.response["candles"]
        ohlc_df = pd.DataFrame(ohlc_dict)
        ohlc_df = ohlc_df[ohlc_df["complete"]]

        ohlcv_df = ohlc_df["mid"].dropna().apply(pd.Series)
        ohlcv_df["volumne"] = ohlc_df["volumne"]
        ohlcv_df.index = ohlc_df["time"]
        ohlcv_df = ohlcv_df.apply(pd.to_numeric)
        ohlcv_df.reset_index(inplace=True)
        ohlcv_df.columns = ["date", "open", "high", "low", "close", "volume"]
        ohlcv_df["date"] = ohlcv_df["date"].apply(lambda x: self._format_date(x))
        return ohlcv_df

    def market_order(self, inst, order_config={}):
        pass

    def _format_date(self, series):
        ddmmyy = series.split("T")[0].split("-")
        return datetime.date(int(ddmmyy[0]), int(ddmmyy[1]), int(ddmmyy[2]))
