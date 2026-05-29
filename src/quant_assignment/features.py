from __future__ import annotations
import pandas as pd, numpy as np

def compute_features(df: pd.DataFrame, symbol: str, latency_ms:int=400)->pd.DataFrame:
    x=df[df.symbol==symbol].sort_values('ts').copy()
    x=x[x['mid']>0]
    dedup_cols=[c for c in ['ts','symbol','bid_price','ask_price','mid'] if c in x.columns]
    x=x.drop_duplicates(subset=dedup_cols)
    x['ret']=np.log(x['mid']).diff()
    x['decision_ts']=x['ts']+pd.to_timedelta(latency_ms, unit='ms')
    x=x.set_index('ts')
    x['rv_1min']=x['ret'].rolling('60s').std()*np.sqrt(252*6.5*60)
    x['ewma_vol']=x['ret'].ewm(span=120, adjust=False).std()*np.sqrt(252*6.5*60)
    x['mom_30s']=x['mid'].pct_change(freq='30s')
    mom_mean=x['mom_30s'].rolling('10min').mean(); mom_std=x['mom_30s'].rolling('10min').std()
    x['mom_z']=(x['mom_30s']-mom_mean)/(mom_std+1e-12)
    return x.reset_index()
