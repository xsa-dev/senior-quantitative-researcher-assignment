import pandas as pd
from quant_assignment.features import compute_features

def test_compute_features_columns():
    df=pd.DataFrame({'ts':pd.date_range('2025-01-01', periods=5, freq='S'), 'symbol':['X']*5,'mid':[1,1.1,1.2,1.1,1.0]})
    out=compute_features(df,'X')
    assert 'rv_1min' in out.columns and 'mom_z' in out.columns
