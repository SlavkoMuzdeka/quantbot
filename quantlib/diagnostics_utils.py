import seaborn as sns
import matplotlib.pyplot as plt

from quantlib.backtest_utils import kpis
from quantlib.general_utils import save_file


def save_backtests(portfolio_df, brokerage_used, sysname, path="./backtests/"):
    portfolio_df, sharpe, drawdown_max, volatility = kpis(df=portfolio_df)
    annotaion = f"{sysname}: \nSharpe: {sharpe} \nDrawdown: {round(drawdown_max, 2)} \nVolatility: {round(volatility, 2)}"

    ax = sns.lineplot(data=portfolio_df["cum ret"], linewidth=2.5)
    ax.annotate(
        annotaion,
        xy=(0.2, 0.8),
        xycoords="axes fraction",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.3),
        ha="center",
        va="center",
        family="serif",
        size="8.6",
    )
    plt.title("Cumulative Returns")
    plt.savefig(f"{path}{brokerage_used}_{sysname}.png", bbox_inches="tight")
    plt.close()

    portfolio_df.to_csv(f"{path}{brokerage_used}_{sysname}.csv")
    save_file(f"{path}{brokerage_used}_{sysname}.obj", portfolio_df)


def save_diagnostics(
    portfolio_df, instruments, brokerage_used, sysname, path="./diagnostics/"
):
    path += f"{sysname}/"
    for inst in instruments:
        portfolio_df[f"{inst} w"].plot()
    plt.title("Instrument weights")
    plt.savefig(f"{path}{brokerage_used}_weights.png", bbox_inches="tight")
    plt.close()

    portfolio_df["leverage"].plot()
    plt.title("Portfolio Leverage")
    plt.savefig(f"{path}{brokerage_used}_leverage.png", bbox_inches="tight")
    plt.close()

    plt.scatter(portfolio_df.index, portfolio_df["capital ret"] * 100)
    plt.title("Return Scatter Plot")
    plt.savefig(f"{path}{brokerage_used}_scatter.png", bbox_inches="tight")
    plt.close()
