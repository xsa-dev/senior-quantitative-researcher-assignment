import pandas as pd
from quant_assignment.order_book import reconstruct_book

def test_reconstruct_book_empty():
    out=reconstruct_book(pd.DataFrame())
    assert 'symbol' in out.columns
