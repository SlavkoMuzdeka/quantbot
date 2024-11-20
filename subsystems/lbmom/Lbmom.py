import json
import numpy as np
import pandas as pd

from quantlib.indicators_cal import adx_series, ema_series
from quantlib.backtest_utils import get_backtest_day_strats, get_strat_scalar


class Lbmom:
    def __init__(self, instruments_config, historical_df, simulation_start, vol_target):
        self.pairs = [
            (188, 292),
            (90, 94),
            (138, 167),
            (37, 289),
            (94, 170),
            (64, 68),
            (167, 208),
            (35, 191),
            (24, 251),
            (24, 179),
            (24, 158),
        ]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)
        self.sysname = "LBMOM"

    def extend_historicals(self, instruments, historical_df):
        new_columns = {}  # Dictionary to collect new columns
        for inst in instruments:
            historical_df[f"{inst} adx"] = adx_series(
                high=historical_df[f"{inst} high"],
                low=historical_df[f"{inst} low"],
                close=historical_df[f"{inst} close"],
                n=14,  # Arbitrary
            )

            for pair in self.pairs:
                new_columns[f"{inst} ema{str(pair)}"] = ema_series(
                    series=historical_df[f"{inst} close"], n=pair[0]
                ) - ema_series(series=historical_df[f"{inst} close"], n=pair[1])

        historical_df = pd.concat([historical_df, pd.DataFrame(new_columns)], axis=1)
        return historical_df

    def run_simulation(self, historical_df):
        # Init parameters
        instruments = self.instruments_config["instruments"]

        # Calculate/pre-process indicators
        historical_df = self.extend_historicals(
            instruments=instruments, historical_df=historical_df
        )

        # Perform simulation
        portfolio_df = pd.DataFrame(
            index=historical_df[self.simulation_start :].index
        ).reset_index()

        portfolio_df.loc[0, "capital"] = 10_000
        is_halted = (
            lambda inst, date: not np.isnan(historical_df.loc[date, f"{inst} active"])
            and (~historical_df[:date].tail(5)[f"{inst} active"]).all()
        )

        """
        Position Sizing with 3 different techniques combined
            1. Strategy Level Scalar for strategy level risk exposure
            2. Volatility targeting scalar for different assets
            3. Voting system to account for degree of "momentum"  
        """

        for i in portfolio_df.index:
            date = portfolio_df.loc[i, "date"]
            strat_scalar = 2  # Default scaling up for strategy

            tradable = [inst for inst in instruments if not is_halted(inst, date)]
            non_tradable = [inst for inst in instruments if inst not in tradable]

            """
            Get PnL and Scalar for Portfolio
            """
            if i != 0:
                date_prev = portfolio_df.loc[i - 1, "date"]
                pnl = get_backtest_day_strats(
                    portfolio_df, instruments, date, date_prev, i, historical_df
                )
                strat_scalar = get_strat_scalar(
                    portfolio_df, 100, self.vol_target, i, strat_scalar
                )

            portfolio_df.loc[i, "strat scalar"] = strat_scalar

            """
            Get Positions for Traded Instruments, Assign 0 to Non-Traded
            """
            for inst in non_tradable:
                portfolio_df.loc[i, f"{inst} units"] = 0
                portfolio_df.loc[i, f"{inst} w"] = 0

            nominal_total = 0
            for inst in tradable:
                votes = np.sum(
                    [
                        1
                        for pair in self.pairs
                        if historical_df.loc[date, f"{inst} ema{str(pair)}"] > 0
                    ]
                )
                forecast = votes / len(self.pairs)
                forecast = (
                    0 if historical_df.loc[date, f"{inst} adx"] < 25 else forecast
                )

                position_vol_target = (
                    (1 / len(tradable))
                    * portfolio_df.loc[i, "capital"]
                    * self.vol_target
                    / np.sqrt(253)
                )
                inst_price = historical_df.loc[date, f"{inst} close"]
                # If the stock has been actively traded in the last 25 days for all days, then use the rolling volatility
                # of stock returns, else use 2.5%.
                percent_ret_vol = (
                    historical_df.loc[date, f"{inst} % ret vol"]
                    if historical_df[:date].tail(25)[f"{inst} active"].all()
                    else 0.025
                )
                dollar_volatility = inst_price * percent_ret_vol
                position = (
                    strat_scalar * forecast * position_vol_target / dollar_volatility
                )

                portfolio_df.loc[i, f"{inst} units"] = position
                nominal_total += abs(position * inst_price)

            for inst in instruments:
                units = portfolio_df.loc[i, f"{inst} units"]
                nominal_inst = abs(units * historical_df.loc[date, f"{inst} close"])
                inst_w = nominal_inst / nominal_total if nominal_total != 0 else None
                portfolio_df.loc[i, f"{inst} w"] = inst_w

            """
            Perform Logging and Calculations 
            """
            portfolio_df.loc[i, "nominal"] = nominal_total
            portfolio_df.loc[i, "leverage"] = (
                portfolio_df.loc[i, "nominal"] / portfolio_df.loc[i, "capital"]
            )

        return portfolio_df

    def get_subsys_pos(self):
        pass
