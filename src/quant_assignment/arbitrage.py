from __future__ import annotations
import pandas as pd, numpy as np

def prepare_gold_pairs(df:pd.DataFrame):
    mids=df.copy(); mids['mid']=(mids.bid_price+mids.ask_price)/2
    mids=mids[mids['mid']>0].drop_duplicates(subset=['ts','symbol','bid_price','ask_price'])
    b3=mids[mids.symbol.str.startswith('GLD',na=False)].copy()
    mo=mids[mids.symbol.str.contains('GOLD',na=False)].copy()
    s1=b3.symbol.value_counts().index[0] if not b3.empty else None
    s2=mo.symbol.value_counts().index[0] if not mo.empty else None
    if not s1 or not s2: return pd.DataFrame(), None, None
    a=b3[b3.symbol==s1][['ts','mid']].sort_values('ts').rename(columns={'mid':'b3_mid'})
    b=mo[mo.symbol==s2][['ts','mid']].sort_values('ts').rename(columns={'mid':'moex_mid'})
    m=pd.merge_asof(a,b,on='ts',direction='nearest',tolerance=pd.Timedelta('2s')).dropna()
    m['raw_spread']=m['b3_mid']-m['moex_mid']
    win=300
    # Use only prior observations for rolling statistics. This is conservative and
    # avoids using the just-observed spread to normalize itself before a signal.
    m['spread_mean']=m['raw_spread'].rolling(win,min_periods=50).mean().shift(1)
    m['spread_std']=m['raw_spread'].rolling(win,min_periods=50).std().shift(1)
    m['zscore']=(m['raw_spread']-m['spread_mean'])/(m['spread_std']+1e-12)
    positions=[]; pos=0
    for z in m['zscore']:
        if pd.isna(z):
            pass
        elif pos == 0 and z > 2:
            pos = -1  # short B3-vs-MOEX spread
        elif pos == 0 and z < -2:
            pos = 1   # long B3-vs-MOEX spread
        elif pos != 0 and abs(z) < 0.5:
            pos = 0
        elif pos == 1 and z < -3:
            pos = 0   # adverse extension stop
        elif pos == -1 and z > 3:
            pos = 0
        positions.append(pos)
    m['position']=positions
    m['signal']=m['position'].diff().fillna(m['position']).astype(int)
    m['spread_change']=m['raw_spread'].diff().fillna(0)
    tc=0.05
    m['trade']=(m['position']!=m['position'].shift(1)).astype(int)
    m['pnl']=m['position'].shift(1).fillna(0)*m['spread_change']-m['trade']*tc
    m['cum_pnl']=m['pnl'].cumsum()
    return m,s1,s2

def metrics(df:pd.DataFrame)->dict:
    if df.empty: return {}
    eq=df['cum_pnl']; dd=(eq-eq.cummax())
    return {'total_return':float(eq.iloc[-1]),'num_trades':int(df['trade'].sum()),'hit_rate':float((df['pnl']>0).mean()),'max_drawdown':float(dd.min())}
