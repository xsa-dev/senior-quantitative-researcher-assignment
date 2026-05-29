from __future__ import annotations
import pandas as pd


def build_snapshot_updates(decoded: pd.DataFrame):
    updates = decoded.copy()
    snap_cols = ['timestamp', 'symbol', 'side', 'price', 'size', 'level', 'source_file', 'decode_status', 'notes']
    snapshot = decoded[['timestamp', 'symbol', 'side', 'price', 'size', 'source_file', 'decode_status', 'notes']].copy()
    snapshot['level'] = None
    snapshot = snapshot[snap_cols]
    return updates, snapshot


def reconstruct_book(snapshot: pd.DataFrame) -> pd.DataFrame:
    cols = [
        'timestamp', 'symbol', 'bid_price_1', 'bid_size_1', 'ask_price_1', 'ask_size_1',
        'mid_price', 'spread', 'book_depth_available', 'source', 'decode_status', 'notes'
    ]
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

    df = snapshot.copy()
    df = df[df['symbol'].notna() & df['price'].notna() & df['side'].isin(['bid', 'ask'])]
    if df.empty:
        return pd.DataFrame(columns=cols)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['size'] = pd.to_numeric(df['size'], errors='coerce')
    df = df[df['price'].notna() & df['size'].notna()].sort_values(['timestamp'])

    # The decoded assignment rows are order-level MBO messages when order_id is
    # present. For snapshot-only rows with no order id, synthesize a stable key
    # from symbol/side/price/source order so they can still contribute to top of
    # book. This is deterministic and never invents prices or sizes.
    books: dict[str, dict[object, dict[str, object]]] = {}
    for idx, r in df.iterrows():
        symbol = str(r['symbol'])
        action = str(r.get('action', 'snapshot')).lower()
        side = str(r['side'])
        price = float(r['price'])
        size = float(r['size'])
        order_id = r.get('order_id')
        missing_order_id = pd.isna(order_id)
        if missing_order_id:
            order_id = f"snapshot:{idx}:{symbol}:{side}:{price}"
        book = books.setdefault(symbol, {})
        if action in {'delete', 'delete_thru', 'delete_from'}:
            if missing_order_id:
                # B3 mass-delete templates do not carry a secondaryOrderID.
                # Apply the side-level clear to all active MBO orders for the
                # instrument rather than popping a synthetic placeholder key.
                for key, order in list(book.items()):
                    if order.get('side') == side:
                        book.pop(key, None)
            else:
                book.pop(order_id, None)
        elif action in {'new', 'change', 'snapshot'}:
            if size > 0:
                book[order_id] = {'side': side, 'price': price, 'size': size, 'timestamp': r['timestamp'], 'source': r.get('source_file')}
            else:
                book.pop(order_id, None)

    rows = []
    for symbol, orders in books.items():
        active = [o for o in orders.values() if o.get('size') and o.get('price')]
        bids = [o for o in active if o['side'] == 'bid']
        asks = [o for o in active if o['side'] == 'ask']
        bid_price = max((float(o['price']) for o in bids), default=None)
        ask_price = min((float(o['price']) for o in asks), default=None)
        bid_size = sum(float(o['size']) for o in bids if float(o['price']) == bid_price) if bid_price is not None else None
        ask_size = sum(float(o['size']) for o in asks if float(o['price']) == ask_price) if ask_price is not None else None
        mid = (bid_price + ask_price) / 2 if bid_price is not None and ask_price is not None else None
        spread = ask_price - bid_price if bid_price is not None and ask_price is not None else None
        last_ts = max((o['timestamp'] for o in active if pd.notna(o.get('timestamp'))), default=pd.NaT)
        rows.append({
            'timestamp': last_ts,
            'symbol': symbol,
            'bid_price_1': bid_price,
            'bid_size_1': bid_size,
            'ask_price_1': ask_price,
            'ask_size_1': ask_size,
            'mid_price': mid,
            'spread': spread,
            'book_depth_available': len(active),
            'source': 'schema_backed_mbo_reconstruction',
            'decode_status': 'schema_backed_reconstructed' if mid is not None else 'schema_backed_partial_book',
            'notes': 'Top of book reconstructed from decoded B3 MBO order events; no price/size values were fabricated.'
        })
    result = pd.DataFrame(rows, columns=cols)
    if not result.empty:
        bid = pd.to_numeric(result['bid_price_1'], errors='coerce')
        ask = pd.to_numeric(result['ask_price_1'], errors='coerce')
        crossed = bid.notna() & ask.notna() & (bid > ask)
        # Crossed states can occur in auction/uncleared local replay windows when
        # not every market-state template is economically decoded. The final
        # reconstructed top-of-book output keeps only non-crossed books so
        # downstream spreads never consume invalid bid/ask pairs.
        result = result.loc[~crossed].copy()
    return result.sort_values(['symbol']).reset_index(drop=True)
