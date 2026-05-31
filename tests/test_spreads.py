import pandas as pd
from quant_assignment.spreads import build_wdo_spread, normalize_book_quotes, build_wdo_top_of_book_timeseries


def test_build_wdo_spread_uses_calendar_order_for_valid_wdo_futures():
    df = pd.DataFrame({
        'ts': pd.to_datetime(['2025-01-01 00:00:00Z', '2025-01-01 00:00:00.5Z'], format='mixed'),
        'symbol': ['WDOG26', 'WDOF26'],
        'bid_price': [5404.0, 5366.0],
        'ask_price': [5405.5, 5366.5],
        'bid_qty': [1, 2],
        'ask_qty': [3, 4],
        'mid': [5404.75, 5366.25],
    })
    out = build_wdo_spread(df)
    assert len(out) == 1
    assert out.loc[0, 'near_contract'] == 'WDOF26'
    assert out.loc[0, 'far_contract'] == 'WDOG26'
    assert out.loc[0, 'near_bid'] == 5366.0
    assert out.loc[0, 'near_ask'] == 5366.5
    assert out.loc[0, 'far_bid'] == 5404.0
    assert out.loc[0, 'far_ask'] == 5405.5
    assert out.loc[0, 'spread'] == 5366.25 - 5404.75
    assert out.loc[0, 'source'] == 'schema_backed_reconstructed_book'
    assert pd.notna(out.loc[0, 'schema_provenance'])


def test_build_wdo_top_of_book_timeseries_replays_mbo_events():
    events = pd.DataFrame([
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOG26', 'message_type': 'Order_MBO', 'side': 'bid', 'price': 5400.0, 'size': 2, 'action': 'new', 'order_id': 'g_bid_1', 'packet_index': 1, 'rpt_seq': 1},
        {'timestamp': '2025-01-01T00:00:01Z', 'symbol': 'WDOG26', 'message_type': 'Order_MBO', 'side': 'ask', 'price': 5402.0, 'size': 3, 'action': 'new', 'order_id': 'g_ask_1', 'packet_index': 2, 'rpt_seq': 2},
        {'timestamp': '2025-01-01T00:00:02Z', 'symbol': 'WDOH26', 'message_type': 'Order_MBO', 'side': 'bid', 'price': 5430.0, 'size': 1, 'action': 'new', 'order_id': 'h_bid_1', 'packet_index': 3, 'rpt_seq': 1},
        {'timestamp': '2025-01-01T00:00:03Z', 'symbol': 'WDOH26', 'message_type': 'Order_MBO', 'side': 'ask', 'price': 5435.0, 'size': 4, 'action': 'new', 'order_id': 'h_ask_1', 'packet_index': 4, 'rpt_seq': 2},
        {'timestamp': '2025-01-01T00:00:04Z', 'symbol': 'WDOG26', 'message_type': 'DeleteOrder_MBO', 'side': 'bid', 'price': 5400.0, 'size': 2, 'action': 'delete', 'order_id': 'g_bid_1', 'packet_index': 5, 'rpt_seq': 3},
    ])
    top = build_wdo_top_of_book_timeseries(events, contracts=('WDOG26', 'WDOH26'))
    assert top['symbol'].tolist() == ['WDOG26', 'WDOH26']
    assert top.loc[0, 'mid'] == 5401.0
    assert top.loc[1, 'mid'] == 5432.5
    assert top['source'].eq('schema_backed_wdo_mbo_timeseries').all()
    spread = build_wdo_spread(top, source='schema_backed_wdo_mbo_timeseries')
    assert len(spread) == 1
    assert spread.loc[0, 'near_contract'] == 'WDOG26'
    assert spread.loc[0, 'far_contract'] == 'WDOH26'
    assert spread.loc[0, 'spread'] == 5401.0 - 5432.5


def test_normalize_book_quotes_filters_crossed_books_and_options():
    book = pd.DataFrame([
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOF26', 'bid_price_1': 5370.0, 'bid_size_1': 1, 'ask_price_1': 5369.0, 'ask_size_1': 1},
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOG26', 'bid_price_1': 5404.0, 'bid_size_1': 1, 'ask_price_1': 5405.5, 'ask_size_1': 1},
    ])
    quotes = normalize_book_quotes(book)
    assert quotes['symbol'].tolist() == ['WDOG26']
    assert quotes.loc[quotes.index[0], 'mid'] == 5404.75
