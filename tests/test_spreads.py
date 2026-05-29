import pandas as pd
from quant_assignment.spreads import build_wdo_spread, normalize_book_quotes


def test_build_wdo_spread_uses_calendar_order_for_valid_wdo_futures():
    df = pd.DataFrame({
        'ts': pd.to_datetime(['2025-01-01 00:00:00Z', '2025-01-01 00:00:00.5Z'], format='mixed'),
        'symbol': ['WDOG26', 'WDOF26'],
        'mid': [5404.75, 5366.25],
    })
    out = build_wdo_spread(df)
    assert len(out) == 1
    assert out.loc[0, 'near_contract'] == 'WDOF26'
    assert out.loc[0, 'far_contract'] == 'WDOG26'
    assert out.loc[0, 'spread'] == 5366.25 - 5404.75


def test_normalize_book_quotes_filters_crossed_books_and_options():
    book = pd.DataFrame([
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOF26', 'bid_price_1': 5370.0, 'bid_size_1': 1, 'ask_price_1': 5369.0, 'ask_size_1': 1},
        {'timestamp': '2025-01-01T00:00:00Z', 'symbol': 'WDOG26', 'bid_price_1': 5404.0, 'bid_size_1': 1, 'ask_price_1': 5405.5, 'ask_size_1': 1},
    ])
    quotes = normalize_book_quotes(book)
    assert quotes['symbol'].tolist() == ['WDOG26']
    assert quotes.loc[quotes.index[0], 'mid'] == 5404.75
