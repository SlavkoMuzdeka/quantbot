import json
import datetime
import pandas as pd
import streamlit as st  # We use streamlit for better visusalisation

from brokerage.oanda.oanda import Oanda
from subsystems.lbmom.Lbmom import Lbmom
from subsystems.lsmom.Lsmom import Lsmom
from dateutil.relativedelta import relativedelta
from quantlib.data_utils import get_sp500_df, extend_dataframe
from quantlib.general_utils import save_file, load_file, load_config, save_config

HISTORICAL_DF_PATH = "Data/historical_df.obj"
PORTFOLIO_CONFIG_PATH = "config/portfolio_config.json"

COUNT = 30
GRANULARITY = "D"

# oanda = Oanda(auth_config=load_config("AUTH"))

# instruments, currencies, cfds, metals = (
#     oanda.get_trade_client().get_account_instruments()
# )
# # Run this first iteration
# save_config(
#     config={"currencies": currencies, "cfds": cfds, "metals": metals},
#     config_name="OANDA",
# )

# # In the second iteration just load saved instruments
# brokerage_config = load_config("OANDA")
# db_instruments = (
#     brokerage_config["currencies"]
#     + brokerage_config["indices"]
#     + brokerage_config["commodities"]
#     + brokerage_config["metals"]
#     + brokerage_config["bonds"]
# )

# database_df = pd.DataFrame()
# for db_inst in db_instruments:
#     df = (
#         oanda.get_trade_client()
#         .get_ohlcv(instrument=db_inst, count=COUNT, granularity=GRANULARITY)
#         .set_index("date")
#     )
#     cols = list(map(lambda x: f"{db_inst} {x}", df.columns))
#     df.columns = cols
#     if len(database_df) == 0:
#         database_df[cols] = df
#     else:
#         database_df.combine_first(df)

# historical_data_oanda = extend_dataframe(
#     instruments=db_instruments, df=database_df, fx_codes=brokerage_config["fx_codes"]
# )


def main():
    """
    Load new data from Yahoo! finance
    """
    # df, instruments = get_sp500_df()
    # df = extend_dataframe(instruments=instruments, df=df)
    # save_file(HISTORICAL_DF_PATH, (df, instruments))

    """
    Load locally saved data
    """
    df, instruments = load_file(HISTORICAL_DF_PATH)

    """
    Risk parameters
    """
    portfolio_config = load_config(PORTFOLIO_CONFIG_PATH)
    vol_target = portfolio_config["vol_target"]
    sim_start = datetime.date.today() - relativedelta(
        years=portfolio_config["sim_years"]
    )

    """
    Subsystem positioning
    """
    subsystems_config = portfolio_config["subsystems"]
    strats = {}

    for subsystem in subsystems_config.keys():
        if subsystem == "lbmom":
            strat = Lbmom(
                instruments_config=portfolio_config["instruments_config"][subsystem],
                historical_df=df,
                simulation_start=sim_start,
                vol_target=vol_target,
            )
        elif subsystem == "lsmom":
            strat = Lsmom(
                instruments_config=portfolio_config["instruments_config"][subsystem],
                historical_df=df,
                simulation_start=sim_start,
                vol_target=vol_target,
            )
        strats[subsystem] = strat

    for _, strat in strats.items():
        df, instruments = strat.get_subsys_pos()
        print(df, instruments)

    # portfolio_df = lbmom.run_simulation(df)
    # print((1 + portfolio_df["capital ret"]).cumprod().iloc[-1])
    # print(portfolio_df)


if __name__ == "__main__":
    main()
