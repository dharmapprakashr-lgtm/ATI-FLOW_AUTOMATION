"""Build the run report: one PDF, in one folder, per test run.

Contents, in order:

1. Header - environment, base URL, when it ran, how long it took
2. Summary - total / passed / failed / skipped / errors / duration / pass rate
3. Results - every test with its outcome and duration
4. Failures - each failure with its error message and its screenshot inline

The screenshots are embedded as base64 data URIs rather than linked, so the PDF
is a single self-contained file you can attach to a ticket without also shipping
an image directory.

The finished PDF is the only artifact kept: it lands in ``reports/`` as
``report_<timestamp>.pdf`` (see ``utils/report_paths.py``). The screenshots and
the summary HTML it is rendered from live in a temporary directory that is
deleted once the PDF exists.
"""

import base64
from datetime import datetime
from html import escape
from pathlib import Path

from utils.report_paths import (  # noqa: E402
    PDF_PATH,
    REPORTS_DIR,
    RUN_STAMP,
    SCREENSHOT_DIR,
    SUMMARY_HTML_PATH as HTML_PATH,
)

#: Outcomes that count as a failure for the summary and the failure section.
FAILED_OUTCOMES = ("failed", "error")

_MAX_MESSAGE_CHARS = 4000


# ── Result collection ─────────────────────────────────────────────────────────

class ResultCollector:
    """Accumulates one record per test as the run progresses."""

    def __init__(self):
        self.results = []
        self.started_at = None
        self.finished_at = None

    def add(self, nodeid, outcome, duration, message=None, screenshot=None):
        existing = next((r for r in self.results if r["nodeid"] == nodeid), None)
        record = {
            "nodeid": nodeid,
            "outcome": outcome,
            "duration": round(duration or 0.0, 2),
            "message": (message or "")[:_MAX_MESSAGE_CHARS],
            "screenshot": str(screenshot) if screenshot else None,
        }
        if existing is None:
            self.results.append(record)
            return
        # A teardown error belongs to the same test, not an extra test result.
        record["duration"] += existing["duration"]
        record["message"] = "\n".join(filter(None, (existing["message"], record["message"])))[:_MAX_MESSAGE_CHARS]
        record["screenshot"] = record["screenshot"] or existing["screenshot"]
        priority = {"passed": 0, "skipped": 1, "xfailed": 2, "xpassed": 3, "failed": 4, "error": 5}
        if priority[existing["outcome"]] > priority[outcome]:
            record["outcome"] = existing["outcome"]
        existing.update(record)

    @property
    def counts(self):
        counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "xfailed": 0, "xpassed": 0}
        for result in self.results:
            counts[result["outcome"]] = counts.get(result["outcome"], 0) + 1
        return counts

    @property
    def failures(self):
        return [r for r in self.results if r["outcome"] in FAILED_OUTCOMES]

    @property
    def duration(self):
        if self.started_at and self.finished_at:
            return max(0.0, self.finished_at - self.started_at)
        return sum(r["duration"] for r in self.results)


# ── Rendering ─────────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0; background: #fff; color: #16191d;
  font: 12px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 21px; margin: 0 0 2px; letter-spacing: -.01em; }
h2 { font-size: 11px; text-transform: uppercase; letter-spacing: .09em; color: #6b7480;
     margin: 26px 0 9px; font-weight: 700; border-bottom: 1px solid #e4e7eb; padding-bottom: 5px; }
.sub { color: #6b7480; font-size: 11px; margin: 0 0 3px; }
.meta { margin: 10px 0 0; font-size: 11px; color: #4a525c; }
.meta span { margin-right: 18px; }

.tiles { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-top: 14px; }
.tile { border: 1px solid #e4e7eb; border-radius: 7px; padding: 10px 11px; background: #fbfcfd; }
.tile .n { font-size: 21px; font-weight: 680; line-height: 1.1; letter-spacing: -.02em; }
.tile .l { font-size: 9px; color: #6b7480; text-transform: uppercase; letter-spacing: .07em; margin-top: 2px; }
.pass { color: #1f8b4c; } .fail { color: #c9372c; } .skip { color: #a8770a; }
.bar { height: 5px; border-radius: 3px; background: #e4e7eb; overflow: hidden; margin-top: 6px; }
.bar > i { display: block; height: 100%; background: #1f8b4c; }
.bar.bad > i { background: #c9372c; }

table { width: 100%; border-collapse: collapse; border: 1px solid #e4e7eb; border-radius: 6px; }
th { text-align: left; font-size: 9px; text-transform: uppercase; letter-spacing: .07em;
     color: #6b7480; padding: 7px 9px; background: #f6f7f9; border-bottom: 1px solid #e4e7eb; font-weight: 700; }
td { padding: 6px 9px; border-bottom: 1px solid #eef0f3; vertical-align: top; font-size: 11px;
     word-wrap: break-word; overflow-wrap: anywhere; }
tr:last-child td { border-bottom: none; }
tr { page-break-inside: avoid; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10.5px; }
.num { text-align: right; white-space: nowrap; }

.badge { display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 9px;
         font-weight: 700; text-transform: uppercase; letter-spacing: .05em; white-space: nowrap; }
.badge.ok   { background: #e3f3e9; color: #1f8b4c; }
.badge.bad  { background: #fbe6e4; color: #c9372c; }
.badge.warn { background: #fdf1d8; color: #a8770a; }

.failure { border: 1px solid #f0d4d1; border-left: 3px solid #c9372c; border-radius: 7px;
           padding: 12px 14px; margin-bottom: 14px; background: #fffbfb; page-break-inside: avoid; }
.failure h3 { font-size: 12px; margin: 0 0 3px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
              word-break: break-all; font-weight: 650; }
.failure .when { font-size: 10px; color: #6b7480; margin-bottom: 8px; }
.trace { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 9.5px;
         line-height: 1.45; white-space: pre-wrap; word-break: break-word; background: #fff;
         border: 1px solid #f0d4d1; border-radius: 5px; padding: 9px 10px; color: #8a2b23; margin: 0 0 10px; }
.shot { margin-top: 8px; }
.shot img { width: 100%; max-width: 100%; height: auto; border: 1px solid #e4e7eb; border-radius: 5px; }
.shot .cap { font-size: 9px; color: #6b7480; margin-top: 4px; text-transform: uppercase; letter-spacing: .06em; }
.empty { border: 1px dashed #d9dee4; border-radius: 7px; padding: 22px; text-align: center;
         color: #6b7480; font-size: 11px; }
.foot { margin-top: 26px; border-top: 1px solid #e4e7eb; padding-top: 9px; color: #8b939d; font-size: 9.5px; }
"""


def _embed_screenshot(path):
    """Return a data URI for the screenshot, or None if unreadable."""
    if not path:
        return None
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return f"data:image/png;base64,{base64.b64encode(data).decode()}"


def _short_id(nodeid):
    """Trim the repo-relative path prefix so the test name stays readable."""
    return nodeid.replace("::", " › ")


def _result_rows(results):
    badge = {"passed": "ok", "failed": "bad", "error": "bad", "skipped": "warn"}
    rows = []
    for result in results:
        cls = badge.get(result["outcome"], "warn")
        rows.append(
            f"<tr><td class='mono'>{escape(_short_id(result['nodeid']))}</td>"
            f"<td><span class='badge {cls}'>{escape(result['outcome'])}</span></td>"
            f"<td class='mono num'>{result['duration']:.2f}s</td>"
            f"<td>{escape(result.get('message') or '') if result['outcome'] in ('skipped', 'xfailed', 'xpassed') else ''}</td></tr>"
        )
    return "\n".join(rows)


def _failure_blocks(failures):
    blocks = []
    for failure in failures:
        message = escape(failure.get("message") or "").strip()
        data_uri = _embed_screenshot(failure.get("screenshot"))

        shot_html = (
            f"<div class='shot'><img src='{data_uri}' alt='failure screenshot'>"
            f"<div class='cap'>Screenshot at failure</div></div>"
            if data_uri else
            "<div class='cap'>No screenshot captured for this failure.</div>"
        )
        blocks.append(
            f"<div class='failure'>"
            f"<h3>{escape(_short_id(failure['nodeid']))}</h3>"
            f"<div class='when'>{escape(failure['outcome'])} after {failure['duration']:.2f}s</div>"
            f"{f'<pre class=trace>{message}</pre>' if message else ''}"
            f"{shot_html}"
            f"</div>"
        )
    return "\n".join(blocks)


def render_html(collector, environment=None, output=HTML_PATH):
    """Write the self-contained summary HTML. Returns its Path."""
    environment = environment or {}
    results = collector.results
    counts = collector.counts

    total = len(results)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0) + counts.get("error", 0)
    skipped = counts.get("skipped", 0)
    duration = collector.duration
    rate = round(100.0 * passed / total, 1) if total else 0.0

    started = (
        datetime.fromtimestamp(collector.started_at).strftime("%Y-%m-%d %H:%M:%S")
        if collector.started_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    failures = collector.failures
    failure_section = (
        _failure_blocks(failures) if failures
        else "<div class='empty'>No unexpected failures recorded. Review skips and expected failures below.</div>"
    )
    results_section = (
        f"<table><tr><th>Test</th><th>Result</th><th class='num'>Duration</th><th>Reason</th></tr>"
        f"{_result_rows(results)}</table>"
        if results else "<div class='empty'>No tests were executed.</div>"
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AtiFlow Automation - Test Run Report</title>
<style>{_CSS}</style>
</head>
<body>
  <h1>AtiFlow Automation - Test Run Report</h1>
  <p class="sub">Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;·&nbsp; run <strong>{escape(RUN_STAMP)}</strong></p>
  <p class="meta">
    <span><strong>Environment:</strong> {escape(str(environment.get('env', 'unknown')))}</span>
    <span><strong>Base URL:</strong> {escape(str(environment.get('base_url', '-')))}</span>
    <span><strong>AtiFlow version:</strong> {escape(str(environment.get("atiflow_version", "Not captured")))}</span>
    <span><strong>Started:</strong> {started}</span>
  </p>

  <h2>Summary</h2>
  <div class="tiles">
    <div class="tile"><div class="n">{total}</div><div class="l">Total tests</div></div>
    <div class="tile"><div class="n pass">{passed}</div><div class="l">Passed</div></div>
    <div class="tile"><div class="n fail">{failed}</div><div class="l">Failed</div></div>
    <div class="tile"><div class="n skip">{skipped}</div><div class="l">Skipped</div></div>
    <div class="tile"><div class="n">{rate}%</div><div class="l">Pass rate</div>
      <div class="bar{'' if failed == 0 else ' bad'}"><i style="width:{rate}%"></i></div></div>
    <div class="tile"><div class="n">{duration:.1f}s</div><div class="l">Duration</div></div>
  </div>

  <p>Expected failures: {counts.get('xfailed', 0)} · Unexpected passes: {counts.get('xpassed', 0)} · Setup/teardown errors: {counts.get('error', 0)}</p>
  <h2>Results ({total})</h2>
  {results_section}

  <h2>Failures ({len(failures)})</h2>
  {failure_section}

  <p class="foot">Generated by <code>utils/pdf_report.py</code>.
     Screenshots are embedded directly in this file.</p>
</body>
</html>
"""

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def build(collector, environment=None, pdf_path=PDF_PATH, keep_html=True):
    """Render the summary and convert it to PDF. Returns (pdf_path, stats)."""
    html_path = render_html(collector, environment)

    # Imported here so a machine without browsers can still produce the HTML.
    from utils.report_to_pdf import html_to_pdf

    # Margins are owned by page.pdf(); a competing @page rule in the CSS makes
    # Chromium draw the running header on top of the content.
    pdf_path, _, _ = html_to_pdf(
        html_path, pdf_path, raw=True,
        margin={"top": "16mm", "bottom": "14mm", "left": "10mm", "right": "10mm"},
    )

    if not keep_html:
        html_path.unlink(missing_ok=True)

    counts = collector.counts
    return pdf_path, {
        "total": len(collector.results),
        "passed": counts.get("passed", 0),
        "failed": counts.get("failed", 0) + counts.get("error", 0),
        "skipped": counts.get("skipped", 0),
        "xfailed": counts.get("xfailed", 0),
        "xpassed": counts.get("xpassed", 0),
        "errors": counts.get("error", 0),
        "duration": round(collector.duration, 2),
        "screenshots": sum(1 for f in collector.failures if f.get("screenshot")),
    }
