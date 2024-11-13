import streamlit as st  # We use streamlit for better visusalisation

from quantlib.general_utils import save_file, load_file
from quantlib.data_utils import get_sp500_df, extend_dataframe

HISTORICAL_DF_PATH = "Data/historical_df.obj"

"""
Run this only first time, if there is no locally data that we will use. 
We do this, because loading info from Yahoo Finance is time consuming
"""
# df, instruments = get_sp500_df()
# df = extend_dataframe(instruments=instruments, df=df)
# save_file(HISTORICAL_DF_PATH, (df, instruments))

df, instruments = load_file(HISTORICAL_DF_PATH)
st.write(df)
st.write(instruments)
