import datetime
import pandas as pd
import yfinance as yf


def get_sp500_df():
    instruments = _get_sp500_instruments()
    ohlcvs = {}

    for inst in instruments:
        inst_df = yf.Ticker(inst).history(period="5y")
        ohlcvs[inst] = inst_df[["Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
    df = pd.DataFrame(index=ohlcvs["MMM"].index)
    df.index.name = "date"

    instruments = list(ohlcvs.keys())
    for inst in instruments:
        inst_df = ohlcvs[inst]
        columns = list(map(lambda x: f"{inst} {x}", inst_df.columns))
        df[columns] = inst_df

    return df, instruments


def extend_dataframe(instruments, df):
    df.index = pd.Series(df.index).apply(lambda x: _format_date(x))

    open_cols = list(map(lambda x: str(x) + " open", instruments))
    high_cols = list(map(lambda x: str(x) + " high", instruments))
    low_cols = list(map(lambda x: str(x) + " low", instruments))
    close_cols = list(map(lambda x: str(x) + " close", instruments))
    volume_cols = list(map(lambda x: str(x) + " volume", instruments))

    historical_data = df.copy()
    historical_data = historical_data[
        open_cols + high_cols + low_cols + close_cols + volume_cols
    ]
    historical_data.ffill(inplace=True)

    for inst in instruments:
        historical_data[f"{inst} % ret"] = (
            historical_data[f"{inst} close"] / historical_data[f"{inst} close"].shift(1)
            - 1
        )
        historical_data[f"{inst} % ret vol"] = (
            historical_data[f"{inst} % ret"].rolling(25).std()
        )
        historical_data[f"{inst} active"] = historical_data[
            f"{inst} close"
        ] != historical_data[f"{inst} close"].shift(1)

    historical_data.bfill(inplace=True)
    return historical_data


def _get_sp500_instruments():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)
    sp500_table = table[0]
    symbols = sp500_table["Symbol"].tolist()
    return symbols[
        :10
    ]  # TODO Change if neccessary - for this case we only get 10 first sybmols from S&P 500 list


def _format_date(dates):
    yymmdd = str(dates).split(" ")[0].split("-")
    return datetime.date(int(yymmdd[0]), int(yymmdd[1]), int(yymmdd[2]))
