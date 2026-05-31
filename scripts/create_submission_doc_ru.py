#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
import os
from io import BytesIO
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
TOKEN = Path.home() / ".hermes" / "google_token_drive_upload.json"
DRIVE_FOLDER_ID = "1bFTa7zj9hZeBhmgAN0aeZqjb3QWKYxHA"
DRIVE_FOLDER_URL = f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}"
GITHUB_URL = "https://github.com/xsa-dev/senior-quantitative-researcher-assignment"
TITLE = "Senior Quantitative Researcher — документация к тестовому заданию"
EXISTING_DOC_ID = "17FHnEeDEcN-3uFHe-J6tAI_y6y9su1lNTST3BWxSLX8"
MAX_DOC_IMAGE_WIDTH_PX = 600

# Links verified from the uploaded Google Drive artifact bundle.
LINKS = {
    "updates.csv": "https://drive.google.com/file/d/1le8xeUuiOE3CGzLUlMg5K4ix4AZfL4cr/view?usp=drivesdk",
    "increment_updates.csv": "https://drive.google.com/file/d/1tINf6pfwnVzA5bZMrDikxTd-SNqxXSZG/view?usp=drivesdk",
    "snapshot.csv": "https://drive.google.com/file/d/1OqZdfhZ40nvhNuIeKs0j2j8qpkPq2zev/view?usp=drivesdk",
    "snapshot_updates.csv": "https://drive.google.com/file/d/1oCJA3S2iwGQn_v9KB35lgtTWFEmhpQ94/view?usp=drivesdk",
    "reconstructed_book.csv": "https://drive.google.com/file/d/1zdYIWKvwjHWmmqEBnsful_3L2WAGW_cT/view?usp=drivesdk",
    "wdo_top_of_book_timeseries.csv": "https://drive.google.com/file/d/1MSayF4HbTa8S8a4LDfonnKN3S_EX0H9J/view?usp=drivesdk",
    "wdo_calendar_spread.csv": "https://drive.google.com/file/d/17BlCfYptp9jfEXWwBWDFf30pdqiF4vG3/view?usp=drivesdk",
    "volatility_momentum.csv": "https://drive.google.com/file/d/1y2_sEbx_NamMLBOvIIb5kiVu_bdPB334/view?usp=drivesdk",
    "gold_arbitrage_signals.csv": "https://drive.google.com/file/d/1OfGzCb8P2iyTtn_q70CffCKQUChH6j--/view?usp=drivesdk",
    "wdo_calendar_spread.png": "https://drive.google.com/file/d/1RhHggZ-OZjKXIYFUrZgO6VKKnrfyF-Zv/view?usp=drivesdk",
    "volatility.png": "https://drive.google.com/file/d/157XATc3EhqvKAvNxMFlM13n5FgV7qejt/view?usp=drivesdk",
    "momentum.png": "https://drive.google.com/file/d/1ot2FbyVJnfx6-5OuiOtxVXFHRQEUvMwI/view?usp=drivesdk",
    "gold_spread.png": "https://drive.google.com/file/d/1nlpTaVnBNmaIMTRxASoFORr7i1miObTX/view?usp=drivesdk",
    "gold_spread_zscore.png": "https://drive.google.com/file/d/1pYff4jUPPlhyu46lstorEUJw-zopQE11/view?usp=drivesdk",
    "gold_arbitrage_signals.png": "https://drive.google.com/file/d/1KgUrKu7kPtlCrNPCE9PZNSjTO1FbLh93/view?usp=drivesdk",
    "validation_report.md": "https://drive.google.com/file/d/1oOwZfv931prSEbg66mjW3V0ZvbeHC8s8/view?usp=drivesdk",
    "summary_metrics.md": "https://drive.google.com/file/d/1aArNG596ha4UCBAAYMrDH8MzF672Jizc/view?usp=drivesdk",
}


def a(label: str, url: str) -> str:
    return f'<a href="{html.escape(url)}">{html.escape(label)}</a>'


def img(path: str, caption: str) -> str:
    p = REPO / "outputs" / "plots" / path
    link = a(path, LINKS[path])
    if not p.exists():
        return f"<p><b>{html.escape(caption)}:</b> {link}</p>"
    with Image.open(p) as im:
        im = im.convert("RGB")
        if im.width > MAX_DOC_IMAGE_WIDTH_PX:
            ratio = MAX_DOC_IMAGE_WIDTH_PX / im.width
            im = im.resize((MAX_DOC_IMAGE_WIDTH_PX, int(im.height * ratio)), Image.Resampling.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="PNG", optimize=True)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        f'<figure><img src="data:image/png;base64,{data}" '
        f'width="{MAX_DOC_IMAGE_WIDTH_PX}" />'
        f'<figcaption>{html.escape(caption)} — {link}</figcaption></figure>'
    )


def html_doc() -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>
body {{ font-family: Arial, sans-serif; line-height: 1.45; color: #111; }}
h1, h2, h3 {{ color: #0b1f3a; }}
code, pre {{ font-family: Menlo, Consolas, monospace; }}
pre {{ background: #f6f8fa; padding: 10px; border-radius: 6px; overflow: auto; }}
li {{ margin-bottom: 4px; }}
.summary {{ background:#eef6ff; padding:12px; border-left:4px solid #2f6feb; }}
.warn {{ background:#fff8e5; padding:12px; border-left:4px solid #d29922; }}
figure {{ margin: 18px 0; }}
figcaption {{ font-size: 90%; color: #444; }}
</style></head><body>

<h1>Senior Quantitative Researcher — документация к тестовому заданию</h1>

<div class="summary">
<p><b>GitHub:</b> {a(GITHUB_URL, GITHUB_URL)}</p>
<p><b>Google Drive с результатами:</b> {a(DRIVE_FOLDER_URL, DRIVE_FOLDER_URL)}</p>
<p><b>Статус:</b> код опубликован отдельно от больших входных/выходных данных. В репозитории хранятся только код, тесты, документация и пустой skeleton папки <code>outputs/</code>; raw <code>documents/</code> и generated artifacts доставляются через Google Drive.</p>
</div>

<h2>1. Что именно сделано</h2>
<p>Проект закрывает четыре пункта задания:</p>
<ol>
<li>разбор B3 PCAP и формирование таблиц <code>snapshot</code>, <code>updates</code>, <code>increment_updates</code>, <code>reconstructed_book</code>;</li>
<li>расчет календарного спреда WDO между выбранными месяцами;</li>
<li>расчет волатильности и momentum с учетом 400 мс latency;</li>
<li>исследовательский прототип стратегии B3/MOEX gold futures arbitrage.</li>
</ol>

<h2>2. Как запускать проект на интервью</h2>
<pre>git clone {GITHUB_URL}.git
cd senior-quantitative-researcher-assignment
make install
make all
make test</pre>
<p>Последняя локальная проверка: <code>14 passed</code>. Полный pipeline регенерирует CSV, plots и validation reports при наличии исходных данных в локальной папке <code>documents/</code>.</p>

<h2>3. Задача 1 — B3 PCAP parsing: snapshot, updates, increment, reconstructed book</h2>
<h3>Требование из задания</h3>
<p>Разобрать архив PCAP с биржи B3 и записать таблицы snapshot и updates; дать ссылку на GitHub, отдельную документацию и CSV с increment, snapshot, сведенным стаканом.</p>

<h3>Решение</h3>
<p>PCAP разбирается в два уровня:</p>
<ul>
<li><b>packet evidence:</b> timestamp, network metadata, payload hashes, frame inventory;</li>
<li><b>schema-backed economic decoding:</b> symbol, security_id, side, price, size, order_id, message type and action from verified B3 UMDF/SBE layouts.</li>
</ul>
<p>Критичный момент: рыночные поля не фабрикуются. Если template не поддержан, строка остается диагностической evidence-записью, а не псевдо-декодированным market event.</p>

<h3>Schema/provenance</h3>
<ul>
<li>Используется совместимый schema artifact <code>b3-market-data-messages-2.2.0.xml</code>.</li>
<li>Локальные PCAP frames проверены по header: <code>&lt;HHHHHH&gt; = msgSize, encoding, blockLen, templateId, schemaId, version</code>.</li>
<li>Наблюдаемый match: <code>encoding=0xeb50</code>, <code>schemaId=2</code>, <code>version=15</code>.</li>
<li>Поддержаны assignment-critical templates: 12 SecurityDefinition, 30 SnapshotFullRefresh_Header, 50 Order_MBO, 51 DeleteOrder_MBO, 52 MassDeleteOrders_MBO, 71 SnapshotFullRefresh_Orders_MBO.</li>
</ul>

<h3>CSV-ссылки для задачи 1</h3>
<ul>
<li>{a('updates.csv', LINKS['updates.csv'])}</li>
<li>{a('increment_updates.csv', LINKS['increment_updates.csv'])}</li>
<li>{a('snapshot.csv', LINKS['snapshot.csv'])}</li>
<li>{a('snapshot_updates.csv', LINKS['snapshot_updates.csv'])}</li>
<li>{a('reconstructed_book.csv', LINKS['reconstructed_book.csv'])}</li>
</ul>

<h2>4. Задача 2 — WDO calendar spread</h2>
<h3>Требование из задания</h3>
<p>Вывести календарный спред между фьючерсами WDO разных месяцев, добавить график, дать GitHub и документацию.</p>

<h3>Решение</h3>
<p>Спред строится не из non-WDO quote CSV и не из одного final snapshot, а из event-driven schema-backed WDO MBO top-of-book time series.</p>
<pre>Selected pair: WDOG26 - WDOH26
WDO top-of-book rows: 38,772
Calendar-spread rows: 21,387
First spread: -32.5</pre>
<p>Метод:</p>
<ol>
<li>декодировать WDO futures instruments из SecurityDefinition;</li>
<li>replay WDO MBO order events в top-of-book states;</li>
<li>оставить только валидные positive bid/ask и <code>bid &lt;= ask</code>;</li>
<li>выбрать near/far contracts по futures month code;</li>
<li>синхронизировать series через <code>merge_asof</code>;</li>
<li>посчитать <code>spread = near_mid - far_mid</code>.</li>
</ol>
<p>CSV: {a('wdo_top_of_book_timeseries.csv', LINKS['wdo_top_of_book_timeseries.csv'])}; {a('wdo_calendar_spread.csv', LINKS['wdo_calendar_spread.csv'])}</p>
{img('wdo_calendar_spread.png', 'График WDO calendar spread')}

<h2>5. Задача 3 — Волатильность и momentum с latency 400 мс</h2>
<h3>Требование из задания</h3>
<p>Написать алгоритм, определяющий волатильность и моментум для выбранных фьючерсов. Вывести графики momentum и volatility. Контекст: от получения market data до выставления заявки проходит 400 мс.</p>

<h3>Решение</h3>
<p>В исходном quote dataset requested <code>WDOG26</code> был недоступен, поэтому выбран наиболее ликвидный доступный symbol <code>GOLD-3.26</code>.</p>
<pre>Rows: 362,448
momentum finite z-score rows: 362,416 / 362,448
realized volatility finite rows: 362,216 / 362,448
EWMA volatility finite rows: 362,446 / 362,448
decision_ts - ts unique milliseconds: [400.0]</pre>
<p>Особенность реализации momentum: ticks нерегулярные, поэтому точный <code>pct_change(freq='30s')</code> приводит к all-NaN. В финальном решении momentum считается через as-of lag: берется последний midpoint, наблюдавшийся не позже <code>ts - 30s</code>. Это сохраняет экономический смысл и предотвращает пустой график.</p>
<p>Latency моделируется явно: <code>decision_ts = ts + 400ms</code>. Все rolling/ewm statistics backward-looking.</p>
<p>CSV: {a('volatility_momentum.csv', LINKS['volatility_momentum.csv'])}</p>
{img('volatility.png', 'График volatility')}
{img('momentum.png', 'График momentum')}

<h2>6. Задача 4 — B3/MOEX gold futures arbitrage</h2>
<h3>Требование из задания</h3>
<p>Описать торговую стратегию, торгующую арбитраж выбранного фьючерса и его аналога на MOEX. Дать GitHub и документацию.</p>

<h3>Решение</h3>
<p>Выбранные инструменты:</p>
<pre>B3:   GLDG26
MOEX: GOLD-3.26</pre>
<p>Стратегия является research prototype, а не production backtest. Она демонстрирует корректную конструкцию relative-value signal:</p>
<ol>
<li>расчет midpoint для B3 и MOEX quotes;</li>
<li>nearest-time alignment с tolerance 2 seconds;</li>
<li><code>raw_spread = b3_mid - moex_mid</code>;</li>
<li>rolling mean/std over 300 observations, shifted by one row для исключения look-ahead;</li>
<li>mean-reversion thresholds: entry at |z| &gt; 2, exit at |z| &lt; 0.5, adverse stop at |z| &gt; 3;</li>
<li>transaction-cost proxy 0.05 per position change;</li>
<li>prototype PnL over spread changes.</li>
</ol>
<pre>Aligned rows: 120,538
Total return: 798.325000
Trades: 4,893
Hit rate: 0.108182
Max drawdown: -53.500000</pre>
<p>CSV: {a('gold_arbitrage_signals.csv', LINKS['gold_arbitrage_signals.csv'])}</p>
{img('gold_spread.png', 'B3-MOEX gold raw spread')}
{img('gold_spread_zscore.png', 'Gold spread z-score')}
{img('gold_arbitrage_signals.png', 'Prototype cumulative PnL')}

<h2>7. Validation и quality controls</h2>
<ul>
<li>required outputs presence;</li>
<li>row counts, missing values, timestamp parsing/ranges/monotonicity;</li>
<li>duplicate full-row checks;</li>
<li>B3 decode-status distribution;</li>
<li>economic fields only with schema provenance;</li>
<li>reconstructed-book bid/ask validity;</li>
<li>WDO non-crossed bid/ask validity and finite spread checks;</li>
<li>volatility/momentum finite-feature checks, чтобы пустые plots не проходили silently;</li>
<li>arbitrage shifted rolling z-score look-ahead control.</li>
</ul>
<p>Reports: {a('validation_report.md', LINKS['validation_report.md'])}; {a('summary_metrics.md', LINKS['summary_metrics.md'])}</p>

<h2>8. Почему большие файлы не лежат в GitHub</h2>
<div class="warn">
<p>В репозитории намеренно хранится только код, тесты, документация и skeleton <code>outputs/</code>. Raw <code>documents/</code>, PCAP archives и generated CSV/plots/reports не коммитятся, потому что часть файлов большая и должна доставляться через Drive. Это снижает риск сломать GitHub limits и делает репозиторий воспроизводимым.</p>
</div>
<p>Полный Drive bundle: {a(DRIVE_FOLDER_URL, DRIVE_FOLDER_URL)}</p>

<h2>9. Ограничения и честные caveats</h2>
<ul>
<li>Декодер экономически поддерживает assignment-critical templates; остальные templates остаются diagnostic evidence до отдельной реализации.</li>
<li>Production-grade B3 book builder потребовал бы полной session-state логики, recovery, feed A/B reconciliation, auction-state handling и полного покрытия templates.</li>
<li>Gold arbitrage PnL — исследовательская диагностика spread signal, а не production strategy: не учтены FX conversion, multipliers, full fees, margins, queue priority, slippage, exchange calendar overlap и execution model.</li>
</ul>

<h2>10. Короткое резюме для интервью</h2>
<p>Я сначала сделал границу B3 PCAP явной, затем решил критичный blocker через schema-backed UMDF/SBE decoding и проверку локальных frame headers. Финальный pipeline декодирует реальные SecurityDefinition и MBO order events, строит WDO instrument master, реконструирует non-crossed top-of-book, считает intraday WDO calendar-spread time series, строит latency-aware volatility/momentum features и добавляет validation checks против пустых/NaN графиков. Unsupported templates не подменяются эвристикой — они остаются диагностикой.</p>

</body></html>"""


def markdown_doc(doc_url: str | None = None) -> str:
    link_lines = "\n".join(f"- [{k}]({v})" for k, v in LINKS.items())
    return f"""# {TITLE}

GitHub: {GITHUB_URL}

Google Doc: {doc_url or 'будет создан через scripts/create_submission_doc_ru.py'}

Google Drive artifacts: {DRIVE_FOLDER_URL}

Этот файл является локальной markdown-копией русскоязычной Google Doc-документации. Полная версия создается скриптом `scripts/create_submission_doc_ru.py` и содержит подробные ответы на `documents/tasks.md`, ссылки на CSV/plots и пояснения по методологии.

## Ключевые ссылки на артефакты

{link_lines}
"""


def upload_doc(html_path: Path) -> tuple[str, str]:
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    drive = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(str(html_path), mimetype="text/html", resumable=True)
    existing_doc_id = os.environ.get("SUBMISSION_DOC_ID", EXISTING_DOC_ID)
    if existing_doc_id:
        created = drive.files().update(
            fileId=existing_doc_id,
            body={"name": TITLE, "mimeType": "application/vnd.google-apps.document"},
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        ).execute()
    else:
        meta = {
            "name": TITLE,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [DRIVE_FOLDER_ID],
        }
        created = drive.files().create(body=meta, media_body=media, fields="id, webViewLink", supportsAllDrives=True).execute()
    drive.permissions().create(
        fileId=created["id"],
        body={"type": "anyone", "role": "reader"},
        fields="id",
        supportsAllDrives=True,
    ).execute()
    final = drive.files().get(fileId=created["id"], fields="id, webViewLink", supportsAllDrives=True).execute()
    return final["id"], final["webViewLink"]


def main() -> None:
    docs = REPO / "docs"
    docs.mkdir(exist_ok=True)
    html_path = docs / "submission_ru.html"
    md_path = docs / "submission_ru.md"
    html_path.write_text(html_doc(), encoding="utf-8")
    doc_id, doc_url = upload_doc(html_path)
    md_path.write_text(markdown_doc(doc_url), encoding="utf-8")
    print(f"DOC_ID={doc_id}")
    print(f"DOC_URL={doc_url}")
    print(f"HTML={html_path}")
    print(f"MD={md_path}")


if __name__ == "__main__":
    main()
