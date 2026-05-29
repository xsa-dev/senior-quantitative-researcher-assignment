import pandas as pd
from quant_assignment.order_book import reconstruct_book


def test_reconstruct_book_empty():
    out = reconstruct_book(pd.DataFrame())
    assert 'symbol' in out.columns


def test_mass_delete_without_order_id_clears_side_before_rebuild():
    events = pd.DataFrame([
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOF26', 'side': 'ask', 'price': 5364.0, 'size': 2, 'action': 'new', 'order_id': 1, 'source_file': 'inc', 'decode_status': 'schema_backed_order_mbo', 'notes': ''},
        {'timestamp': '2025-01-01T00:00:01Z', 'symbol': 'WDOF26', 'side': 'ask', 'price': 5364.0, 'size': 0, 'action': 'delete_from', 'order_id': pd.NA, 'source_file': 'inc', 'decode_status': 'schema_backed_mass_delete_mbo', 'notes': ''},
        {'timestamp': '2025-01-01T00:00:02Z', 'symbol': 'WDOF26', 'side': 'ask', 'price': 5370.0, 'size': 3, 'action': 'new', 'order_id': 2, 'source_file': 'inc', 'decode_status': 'schema_backed_order_mbo', 'notes': ''},
        {'timestamp': '2025-01-01T00:00:03Z', 'symbol': 'WDOF26', 'side': 'bid', 'price': 5368.5, 'size': 4, 'action': 'new', 'order_id': 3, 'source_file': 'inc', 'decode_status': 'schema_backed_order_mbo', 'notes': ''},
    ])
    out = reconstruct_book(events)
    row = out[out['symbol'] == 'WDOF26'].iloc[0]
    assert row['bid_price_1'] == 5368.5
    assert row['ask_price_1'] == 5370.0


def test_reconstruct_book_excludes_crossed_final_top_of_book_rows():
    events = pd.DataFrame([
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOF26', 'side': 'ask', 'price': 5364.0, 'size': 2, 'action': 'new', 'order_id': 1, 'source_file': 'inc', 'decode_status': 'schema_backed_order_mbo', 'notes': ''},
        {'timestamp': '2025-01-01T00:00:01Z', 'symbol': 'WDOF26', 'side': 'bid', 'price': 5368.5, 'size': 4, 'action': 'new', 'order_id': 2, 'source_file': 'inc', 'decode_status': 'schema_backed_order_mbo', 'notes': ''},
    ])
    out = reconstruct_book(events)
    assert 'WDOF26' not in out['symbol'].tolist()
