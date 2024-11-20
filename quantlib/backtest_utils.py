import numpy as np
import pandas as pd


def get_backtest_day_strats(
    portfolio_df, instruments, date, date_prev, date_idx, historical_df
):
    day_pnl = 0
    nominal_ret = 0

    for inst in instruments:
        previous_holdings = portfolio_df.loc[date_idx - 1, f"{inst} units"]
        if previous_holdings != 0:
            price_change = (
                historical_df.loc[date, f"{inst} close"]
                - historical_df.loc[date_prev, f"{inst} close"]
            )
            dollar_change = price_change * 1
            inst_pnl = dollar_change * previous_holdings
            day_pnl += inst_pnl
            nominal_ret += (
                portfolio_df.loc[date_idx - 1, f"{inst} w"]
                * historical_df.loc[date, f"{inst} % ret"]
            )

    capital_ret = nominal_ret * portfolio_df.loc[date_idx - 1, "leverage"]
    portfolio_df.loc[date_idx, "capital"] = (
        portfolio_df.loc[date_idx - 1, "capital"] + day_pnl
    )
    portfolio_df.loc[date_idx, "daily pnl"] = day_pnl
    portfolio_df.loc[date_idx, "nominal ret"] = nominal_ret
    portfolio_df.loc[date_idx, "capital ret"] = capital_ret

    return day_pnl


def get_strat_scalar(portfolio_df, lookback, vol_target, idx, default):
    capital_ret_history = portfolio_df.loc[:idx].dropna().tail(lookback)["capital ret"]
    start_scaler_history = (
        portfolio_df.loc[:idx].dropna().tail(lookback)["strat scalar"]
    )

    if len(capital_ret_history) == lookback:
        annualized_vol = capital_ret_history.std() * np.sqrt(253)
        scalar_hist_avg = np.mean(start_scaler_history)
        strat_scalar = scalar_hist_avg * vol_target / annualized_vol
        return strat_scalar
    else:
        return default
