from pathlib import Path
import pandas as pd

from quant_assignment.validation import validate_outputs


def test_validation_reports_wdo_spread_schema_provenance(tmp_path: Path):
    csvd = tmp_path / 'csv'
    csvd.mkdir(parents=True)
    minimal = pd.DataFrame({'timestamp': [], 'symbol': []})
    for name in ['updates.csv', 'snapshot.csv', 'reconstructed_book.csv', 'volatility_momentum.csv', 'gold_arbitrage_signals.csv']:
        minimal.to_csv(csvd / name, index=False)
    pd.DataFrame([{
        'ts': '2025-01-01T00:00:00Z',
        'spread': -32.5,
        'near_contract': 'WDOG26',
        'far_contract': 'WDOH26',
        'near_bid': 5404.0,
        'near_ask': 5405.5,
        'near_mid': 5404.75,
        'far_bid': 5435.5,
        'far_ask': 5439.0,
        'far_mid': 5437.25,
        'source': 'schema_backed_reconstructed_book',
        'schema_provenance': 'B3 UMDF/SBE decoded MBO top-of-book',
    }]).to_csv(csvd / 'wdo_calendar_spread.csv', index=False)

    report = validate_outputs(tmp_path)
    assert '- WDO spread source schema-backed: True' in report
    assert '- WDO spread schema provenance present: True' in report
