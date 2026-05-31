from __future__ import annotations
from collections import defaultdict
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


def build_wdo_top_of_book_timeseries(
    events: pd.DataFrame,
    contracts: tuple[str, ...] = ('WDOG26', 'WDOH26'),
) -> pd.DataFrame:
    """Replay decoded WDO MBO order events into a non-crossed top-of-book time series.

    This intentionally consumes only schema-backed decoded order fields. It emits a
    row after each event for which the contract has a positive, non-crossed two-sided
    book. Prices, sizes, and order IDs come directly from decoded B3 UMDF/SBE rows.
    """
    cols = [
        'ts', 'symbol', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty',
        'mid', 'book_spread', 'book_depth_available', 'source', 'schema_provenance'
    ]
    if events.empty:
        return pd.DataFrame(columns=cols)
    needed = {'timestamp', 'symbol', 'message_type', 'side', 'price', 'size', 'action', 'order_id'}
    if not needed.issubset(events.columns):
        return pd.DataFrame(columns=cols)

    df = events.copy()
    df = df[df['symbol'].astype(str).isin(contracts)]
    df = df[df['message_type'].isin(['Order_MBO', 'DeleteOrder_MBO'])]
    df = df[df['side'].isin(['bid', 'ask']) & df['order_id'].notna()]
    if df.empty:
        return pd.DataFrame(columns=cols)
    df['ts'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['size'] = pd.to_numeric(df['size'], errors='coerce')
    sort_cols = [c for c in ['ts', 'packet_index', 'rpt_seq'] if c in df.columns]
    df = df.dropna(subset=['ts']).sort_values(sort_cols or ['ts'])

    books: dict[str, dict[object, dict[str, float | str]]] = defaultdict(dict)
    rows: list[dict[str, object]] = []
    for r in df.itertuples(index=False):
        symbol = str(r.symbol)
        book = books[symbol]
        order_id = r.order_id
        action = str(getattr(r, 'action', '')).lower()
        message_type = str(getattr(r, 'message_type', ''))
        if message_type == 'DeleteOrder_MBO' or action.startswith('delete'):
            book.pop(order_id, None)
        elif message_type == 'Order_MBO' and pd.notna(r.price) and pd.notna(r.size):
            size = float(r.size)
            if size > 0:
                book[order_id] = {'side': str(r.side), 'price': float(r.price), 'size': size}
            else:
                book.pop(order_id, None)

        active = [o for o in book.values() if float(o.get('size', 0) or 0) > 0]
        bids = [o for o in active if o.get('side') == 'bid']
        asks = [o for o in active if o.get('side') == 'ask']
        bid = max((float(o['price']) for o in bids), default=None)
        ask = min((float(o['price']) for o in asks), default=None)
        if bid is None or ask is None or bid <= 0 or ask <= 0 or bid > ask:
            continue
        bid_qty = sum(float(o['size']) for o in bids if float(o['price']) == bid)
        ask_qty = sum(float(o['size']) for o in asks if float(o['price']) == ask)
        rows.append({
            'ts': r.ts,
            'symbol': symbol,
            'bid_price': bid,
            'bid_qty': bid_qty,
            'ask_price': ask,
            'ask_qty': ask_qty,
            'mid': (bid + ask) / 2,
            'book_spread': ask - bid,
            'book_depth_available': len(active),
            'source': 'schema_backed_wdo_mbo_timeseries',
            'schema_provenance': 'B3 UMDF/SBE decoded WDO MBO order-event replay; rows emitted only for positive non-crossed two-sided books',
        })
    return pd.DataFrame(rows, columns=cols).drop_duplicates().reset_index(drop=True)


def build_wdo_spread(df: pd.DataFrame, tolerance: pd.Timedelta | str = pd.Timedelta('5s'), source: str = 'schema_backed_reconstructed_book') -> pd.DataFrame:
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
    m['source'] = source
    m['schema_provenance'] = 'B3 UMDF/SBE decoded MBO top-of-book time series; bid/ask rows filtered for bid<=ask before calendar-spread alignment' if source == 'schema_backed_wdo_mbo_timeseries' else 'B3 UMDF/SBE decoded MBO top-of-book; bid/ask rows filtered for bid<=ask before calendar-spread alignment'
    return m[columns].drop_duplicates().reset_index(drop=True)
