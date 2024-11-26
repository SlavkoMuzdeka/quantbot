import numpy as np


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


def set_leverage_cap(
    portfolio_df, instruments, date, idx, nominal_tot, leverage_cap, historical_data
):
    leverage = nominal_tot / portfolio_df.loc[idx, "capital"]
    if leverage > leverage_cap:
        new_nominals = 0
        leverage_scalar = leverage_cap / leverage
        for inst in instruments:
            newpos = portfolio_df.loc[idx, f"{inst} units"] * leverage_scalar
            portfolio_df.loc[idx, f"{inst} units"] = newpos
            if newpos != 0:
                new_nominals += abs(newpos * historical_data.loc[date, f"{inst} close"])
        return new_nominals
    else:
        return nominal_tot


def kpis(df):
    portfolio_df = df.copy()
    portfolio_df["cum ret"] = (1 + portfolio_df["capital ret"]).cumprod()
    portfolio_df["drawdown"] = (
        portfolio_df["cum ret"] / portfolio_df["cum ret"].cummax() - 1
    )
    sharpe = (
        portfolio_df["capital ret"].mean()
        / portfolio_df["capital ret"].std()
        * np.sqrt(253)
    )
    drawdown_max = portfolio_df["drawdown"].min() * 100
    volatility = portfolio_df["capital ret"].std() * np.sqrt(253) * 100
    return portfolio_df, sharpe, drawdown_max, volatility
