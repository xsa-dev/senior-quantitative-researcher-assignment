import pandas as pd
from quant_assignment.arbitrage import prepare_gold_pairs

def test_prepare_gold_pairs():
    df=pd.DataFrame({'ts':pd.date_range('2025-01-01', periods=10, freq='S').tolist()*2,'symbol':['GLDG26']*10+['GOLD-3.26']*10,'bid_price':[100]*20,'ask_price':[101]*20,'bid_qty':[1]*20,'ask_qty':[1]*20})
    out,_,_=prepare_gold_pairs(df)
    assert 'zscore' in out.columns
