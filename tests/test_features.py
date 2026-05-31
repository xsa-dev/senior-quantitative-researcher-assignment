import pandas as pd
from quant_assignment.features import compute_features


def test_compute_features_columns():
    df=pd.DataFrame({'ts':pd.date_range('2025-01-01', periods=5, freq='s'), 'symbol':['X']*5,'mid':[1,1.1,1.2,1.1,1.0]})
    out=compute_features(df,'X')
    assert 'rv_1min' in out.columns and 'mom_z' in out.columns


def test_momentum_uses_asof_lag_for_irregular_ticks():
    df = pd.DataFrame({
        'ts': pd.to_datetime([
            '2025-01-01 00:00:00.100',
            '2025-01-01 00:00:10.200',
            '2025-01-01 00:00:31.000',
            '2025-01-01 00:00:45.500',
            '2025-01-01 00:01:05.000',
        ], utc=True),
        'symbol': ['X'] * 5,
        'mid': [100.0, 101.0, 103.0, 106.0, 107.0],
    })
    out = compute_features(df, 'X')
    assert out['mom_30s'].notna().sum() >= 3
    assert out['mom_z'].notna().sum() >= 2
