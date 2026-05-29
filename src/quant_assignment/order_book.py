from __future__ import annotations
import pandas as pd

def build_snapshot_updates(decoded: pd.DataFrame):
    updates=decoded.copy()
    snap_cols=['timestamp','symbol','side','price','size','level','source_file','decode_status','notes']
    snapshot=decoded[['timestamp','symbol','side','price','size','source_file','decode_status','notes']].copy()
    snapshot['level']=None
    snapshot=snapshot[snap_cols]
    return updates,snapshot

def reconstruct_book(snapshot: pd.DataFrame) -> pd.DataFrame:
    cols=['timestamp','symbol','bid_price_1','bid_size_1','ask_price_1','ask_size_1','mid_price','spread','book_depth_available','source','decode_status','notes']
    if snapshot.empty:
        return pd.DataFrame(columns=cols)
    if 'price' not in snapshot.columns or snapshot['price'].notna().sum() == 0:
        ts = snapshot['timestamp'].min() if 'timestamp' in snapshot.columns and not snapshot.empty else None
        return pd.DataFrame([{
            'timestamp': ts,
            'symbol': None,
            'bid_price_1': None,
            'bid_size_1': None,
            'ask_price_1': None,
            'ask_size_1': None,
            'mid_price': None,
            'spread': None,
            'book_depth_available': 0,
            'source': 'not_reconstructed_b3_schema_missing',
            'decode_status': 'not_reconstructed',
            'notes': 'Order book cannot be reconstructed because price/side/size fields were not decoded from B3 payloads.'
        }], columns=cols)
    g=snapshot.sort_values('timestamp').groupby('symbol', as_index=False).tail(1)
    rows=[]
    for r in g.itertuples(index=False):
        rows.append({'timestamp':r.timestamp,'symbol':r.symbol,'bid_price_1':None,'bid_size_1':None,'ask_price_1':None,'ask_size_1':None,'mid_price':None,'spread':None,'book_depth_available':0,'source':r.source_file,'decode_status':getattr(r,'decode_status',None),'notes':getattr(r,'notes','')})
    return pd.DataFrame(rows, columns=cols)
