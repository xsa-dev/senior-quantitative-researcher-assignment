from __future__ import annotations
import pandas as pd

def load_quotes(path:str)->pd.DataFrame:
    rows=[]
    with open(path,'r',encoding='utf-8-sig',errors='ignore') as f:
        for i,line in enumerate(f):
            line=line.strip()
            if not line:
                continue
            parts=[p.strip().strip('"') for p in line.split(';')]
            if i==0 and parts and parts[0].lower()=='ts':
                continue
            if len(parts)<6:
                continue
            rows.append(parts[:6])
    df=pd.DataFrame(rows, columns=['ts','symbol','bid_price','bid_qty','ask_price','ask_qty'])
    df['ts']=pd.to_datetime(df['ts'], errors='coerce')
    for c in ['bid_price','ask_price','bid_qty','ask_qty']:
        df[c]=pd.to_numeric(df[c], errors='coerce')
    df=df.dropna(subset=['ts','symbol'])
    # Keep only economically valid top-of-book rows. This prevents downstream
    # research from using stale/placeholder zero quotes or crossed quotes.
    df=df[(df['bid_price']>0) & (df['ask_price']>0) & (df['bid_price']<=df['ask_price'])]
    df['mid']=(df['bid_price']+df['ask_price'])/2
    return df

def build_wdo_spread(df:pd.DataFrame)->pd.DataFrame:
    w=df[df['symbol'].str.startswith('WDO', na=False)].copy()
    syms=w['symbol'].value_counts()
    if len(syms)<2:
        return pd.DataFrame(columns=['ts','spread','near_contract','far_contract'])
    s1,s2=list(syms.index[:2])
    a=w[w.symbol==s1][['ts','mid']].rename(columns={'mid':s1})
    b=w[w.symbol==s2][['ts','mid']].rename(columns={'mid':s2})
    m=pd.merge_asof(a.sort_values('ts'), b.sort_values('ts'), on='ts', direction='nearest', tolerance=pd.Timedelta('1s')).dropna()
    m['spread']=m[s1]-m[s2]
    m['near_contract']=s1; m['far_contract']=s2
    return m
