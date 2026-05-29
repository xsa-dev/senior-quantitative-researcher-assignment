from __future__ import annotations
import re
import pandas as pd

_MONTH_ORDER = {c: i for i, c in enumerate("FGHJKMNQUVXZ", start=1)}
_WDO_FUT_RE = re.compile(r"^WDO([FGHJKMNQUVXZ])(\d{2})$")


def load_quotes(path: str) -> pd.DataFrame:
    rows = []
    with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip().strip('"') for p in line.split(';')]
            if i == 0 and parts and parts[0].lower() == 'ts':
                continue
            if len(parts) < 6:
                continue
            rows.append(parts[:6])
    df = pd.DataFrame(rows, columns=['ts', 'symbol', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty'])
    df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
    for c in ['bid_price', 'ask_price', 'bid_qty', 'ask_qty']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['ts', 'symbol'])
    # Keep only economically valid top-of-book rows. This prevents downstream
    # research from using stale/placeholder zero quotes or crossed quotes.
    df = df[(df['bid_price'] > 0) & (df['ask_price'] > 0) & (df['bid_price'] <= df['ask_price'])]
    df['mid'] = (df['bid_price'] + df['ask_price']) / 2
    return df


def _wdo_contract_sort_key(symbol: str) -> tuple[int, int, str]:
    m = _WDO_FUT_RE.match(str(symbol))
    if not m:
        return (9999, 99, str(symbol))
    month_code, yy = m.groups()
    year = 2000 + int(yy)
    return (year, _MONTH_ORDER[month_code], str(symbol))


def normalize_book_quotes(book: pd.DataFrame) -> pd.DataFrame:
    """Convert reconstructed_book.csv rows into quote rows for spread research."""
    if book.empty:
        return pd.DataFrame(columns=['ts', 'symbol', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty', 'mid'])
    rename = {
        'timestamp': 'ts',
        'bid_price_1': 'bid_price',
        'bid_size_1': 'bid_qty',
        'ask_price_1': 'ask_price',
        'ask_size_1': 'ask_qty',
    }
    df = book.rename(columns=rename).copy()
    needed = ['ts', 'symbol', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty']
    for c in needed:
        if c not in df.columns:
            return pd.DataFrame(columns=['ts', 'symbol', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty', 'mid'])
    df = df[needed]
    df['ts'] = pd.to_datetime(df['ts'], errors='coerce', utc=True)
    for c in ['bid_price', 'ask_price', 'bid_qty', 'ask_qty']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['ts', 'symbol', 'bid_price', 'ask_price'])
    df = df[(df['bid_price'] > 0) & (df['ask_price'] > 0) & (df['bid_price'] <= df['ask_price'])]
    df['mid'] = (df['bid_price'] + df['ask_price']) / 2
    return df


def build_wdo_spread(df: pd.DataFrame, tolerance: pd.Timedelta | str = pd.Timedelta('5s')) -> pd.DataFrame:
    columns = [
        'ts', 'spread', 'near_contract', 'far_contract',
        'near_bid', 'near_ask', 'near_mid', 'far_bid', 'far_ask', 'far_mid',
        'source', 'schema_provenance'
    ]
    tolerance = pd.Timedelta(tolerance)
    w = df[df['symbol'].astype(str).str.match(_WDO_FUT_RE, na=False)].copy()
    if w.empty:
        return pd.DataFrame(columns=columns)
    contracts = sorted(w['symbol'].dropna().unique(), key=_wdo_contract_sort_key)
    if len(contracts) < 2:
        return pd.DataFrame(columns=columns)
    s1, s2 = contracts[:2]
    quote_cols = ['ts', 'bid_price', 'ask_price', 'mid']
    for c in quote_cols:
        if c not in w.columns:
            return pd.DataFrame(columns=columns)
    a = w[w.symbol == s1][quote_cols].rename(columns={
        'bid_price': 'near_bid', 'ask_price': 'near_ask', 'mid': 'near_mid'
    }).sort_values('ts')
    b = w[w.symbol == s2][quote_cols].rename(columns={
        'bid_price': 'far_bid', 'ask_price': 'far_ask', 'mid': 'far_mid'
    }).sort_values('ts')
    m = pd.merge_asof(a, b, on='ts', direction='nearest', tolerance=tolerance).dropna()
    m['spread'] = m['near_mid'] - m['far_mid']
    m['near_contract'] = s1
    m['far_contract'] = s2
    m['source'] = 'schema_backed_reconstructed_book'
    m['schema_provenance'] = 'B3 UMDF/SBE decoded MBO top-of-book; bid/ask rows filtered for bid<=ask before calendar-spread alignment'
    return m[columns]
