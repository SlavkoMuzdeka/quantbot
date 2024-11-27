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
from quantlib.backtest_utils import (
    get_backtest_day_strats,
    get_strat_scalar,
    set_leverage_cap,
)
from quantlib.diagnostics_utils import save_backtests, save_diagnostics

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


def run_simulation(
    instruments,
    historical_data,
    portfolio_vol,
    subsystems_dict,
    subsystems_weights,
):
    """
    Init & Pre-processing
    """
    test_ranges = []
    for subsystem in subsystems_dict.keys():
        test_ranges.append(subsystems_dict[subsystem]["strat_df"].index)
    start = max(test_ranges, key=lambda x: [0])[0]

    portfolio_df = pd.DataFrame(index=historical_data[start:].index).reset_index()
    portfolio_df.loc[0, "capital"] = 10_000

    for i in portfolio_df.index:
        date = portfolio_df.loc[i, "date"]
        strat_scalar = 2

        """
        Get PnL and Scalar for Portfolio
        """

        if i != 0:
            date_prev = portfolio_df.loc[i - 1, "date"]
            pnl = get_backtest_day_strats(
                portfolio_df, instruments, date, date_prev, i, historical_data
            )
            strat_scalar = get_strat_scalar(
                portfolio_df, 100, portfolio_vol, i, strat_scalar
            )

        portfolio_df.loc[i, "strat scalar"] = strat_scalar

        inst_units = {}
        for inst in instruments:
            inst_dict = {}
            for subsystem in subsystems_dict.keys():
                subdf = subsystems_dict[subsystem]["strat_df"]
                subunits = (
                    subdf.loc[date, f"{inst} units"]
                    if f"{inst} units" in subdf.columns
                    else 0
                )
                subscalar = (
                    portfolio_df.loc[i, "capital"] / subdf.loc[date, "capital"]
                    if date in subdf.index
                    else 0
                )
                inst_dict[subsystem] = subunits * subscalar
            inst_units[inst] = inst_dict

        nominal_total = 0
        for inst in instruments:
            combined_sizing = 0
            for subsystem in subsystems_dict.keys():
                combined_sizing += (
                    inst_units[inst][subsystem] * subsystems_weights[subsystem]
                )
            position = combined_sizing * strat_scalar
            portfolio_df.loc[i, f"{inst} units"] = position
            if position != 0:
                nominal_total += abs(
                    position * historical_data.loc[date, f"{inst} close"]
                )

        for inst in instruments:
            units = portfolio_df.loc[i, f"{inst} units"]
            if units != 0:
                nominal_inst = units * historical_data.loc[date, f"{inst} close"]
                inst_w = nominal_inst / nominal_total
                portfolio_df.loc[i, f"{inst} w"] = inst_w
            else:
                portfolio_df.loc[i, f"{inst} w"] = 0

        set_leverage_cap(
            portfolio_df=portfolio_df,
            instruments=instruments,
            date=date,
            idx=i,
            nominal_tot=nominal_total,
            leverage_cap=5,
            historical_data=historical_data,
        )
        portfolio_df.loc[i, "nominal"] = nominal_total
        portfolio_df.loc[i, "leverage"] = (
            portfolio_df.loc[i, "nominal"] / portfolio_df.loc[i, "capital"]
        )

    portfolio_df.set_index("date", inplace=True)

    save_backtests(
        portfolio_df=portfolio_df,
        brokerage_used="oan",
        sysname="COMBINED_STRAT",
    )

    save_diagnostics(
        portfolio_df=portfolio_df,
        instruments=instruments,
        brokerage_used="oan",
        sysname="COMBINED_STRAT",
    )
    return portfolio_df


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
    Get Existing Positions & Capital
    """
    brokerage = Oanda(auth_config=load_config("AUTH"))
    positions = brokerage.get_trade_client().get_account_positions()
    capital = brokerage.get_trade_client().get_account_capital()

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

    subsystems_dict = {}
    traded = []
    for k, v in strats.items():
        strat_df, strat_inst = v.get_subsys_pos()
        print(strat_df)
        subsystems_dict[k] = {"strat_df": strat_df, "strat_inst": strat_inst}
        traded += strat_inst

    traded = list(set(traded))
    portfolio_df = run_simulation(
        instruments=traded,
        historical_data=df,
        portfolio_vol=vol_target,
        subsystems_dict=subsystems_dict,
        subsystems_weights=subsystems_config,
    )
    print(portfolio_df)

    """
    Live Optimal Portfolio Allocations
    """
    trade_on_date = portfolio_df.index[-1]
    capital_scalar = capital_scalar / portfolio_df.loc[trade_on_date, "capital"]
    portfolio_optimal = {}

    for inst in traded:
        unscaled_optimal = portfolio_df.loc[trade_on_date, f"{inst} units"]
        scaled_units = unscaled_optimal * capital_scalar
        portfolio_optimal[inst] = {
            "unscaled": unscaled_optimal,
            "scaled_units": scaled_units,
            "rounded_units": round(scaled_units),
            "nominal_exposure": (
                abs(scaled_units * df.loc[trade_on_date, f"{inst} close"])
                if scaled_units != 0
                else 0
            ),
        }

    instruments_held = positions.keys()
    instruments_unheld = [inst for inst in traded if inst not in instruments_held]

    for inst_held in instruments_held:
        order_config = brokerage.get_service_client().get_order_spec(
            inst=inst,
            scaled_units=portfolio_optimal[inst_held]["scaled_units"],
            current_contracts=float(positions[inst_held]),
        )

        required_change = round(
            order_config["rounded_contracts"] - order_config["current_contracts"], 2
        )
        percent_change = round(
            abs(required_change / order_config["current_contracts"]), 3
        )
        is_inertia_overriden = brokerage.get_service_client().is_intertia_overriden(
            percentage_change=percent_change
        )

        if is_inertia_overriden:
            if portfolio_config["order_enabled"]:
                brokerage.get_trade_client().market_order(
                    inst=inst, order_config=order_config
                )

    for inst_unheld in instruments_unheld:
        order_config = brokerage.get_service_client().get_order_spec(
            inst=inst_unheld,
            scaled_units=portfolio_optimal[inst_unheld]["scaled_units"],
            current_contracts=0,
        )

        if order_config["rounded_contracts"] != 0:
            if portfolio_config["order_enabled"]:
                brokerage.get_trade_client().market_order(
                    inst=inst_unheld, order_config=order_config
                )


if __name__ == "__main__":
    main()
