import json
import streamlit as st  # We use streamlit for better visusalisation

from brokerage.oanda.oanda import Oanda
from subsystems.lbmom.Lbmom import Lbmom
from dateutil.relativedelta import relativedelta
from quantlib.general_utils import save_file, load_file
from quantlib.data_utils import get_sp500_df, extend_dataframe

VOL_TARGET = 0.2  # We are targetting 20% annualized vol
AUTH_CONFIG_PATH = "config/auth_config.json"
HISTORICAL_DF_PATH = "Data/historical_df.obj"


with open(AUTH_CONFIG_PATH, "rb") as f:
    auth_config = json.load(f)

oanda = Oanda(auth_config=auth_config)
exit()


"""
Run this only first time, if there is no locally data that we will use. 
We do this, because loading info from Yahoo Finance is time consuming
"""
# df, instruments = get_sp500_df()
# df = extend_dataframe(instruments=instruments, df=df)
# save_file(HISTORICAL_DF_PATH, (df, instruments))

df, instruments = load_file(HISTORICAL_DF_PATH)

sim_start = df.index[-1] - relativedelta(year=3)
lbmom = Lbmom(
    instruments_config="./subsystems/lbmom/config.json",
    historical_df=df,
    simulation_start=sim_start,
    vol_target=VOL_TARGET,
)

df = lbmom.run_simulation(df)
# df.to_csv("see.csv", index=False)
print(df)
