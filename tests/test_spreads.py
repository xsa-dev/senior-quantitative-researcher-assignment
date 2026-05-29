import pandas as pd
from quant_assignment.spreads import build_wdo_spread

def test_build_wdo_spread_basic():
    df=pd.DataFrame({'ts':pd.to_datetime(['2025-01-01','2025-01-01 00:00:01'], format='mixed'), 'symbol':['WDOA','WDOB'], 'mid':[1.0,2.0]})
    out=build_wdo_spread(df)
    assert 'spread' in out.columns or out.empty
