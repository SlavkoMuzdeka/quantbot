import json
import pandas as pd

from quantlib.indicators_cal import adx_series, ema_series, sma_series


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
        for inst in instruments:
            historical_df[f"{inst} adx"] = adx_series(
                high=historical_df[f"{inst} high"],
                low=historical_df[f"{inst} low"],
                close=historical_df[f"{inst} close"],
                n=14,  # Arbitrary
            )

            for pair in self.pairs:
                historical_df[f"{inst} ema{str(pair)}"] = ema_series(
                    series=historical_df[f"{inst} close"], n=pair[0]
                ) - ema_series(series=historical_df[f"{inst} close"], n=pair[1])

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

        print(portfolio_df)

    def get_subsys_pos(self):
        pass
