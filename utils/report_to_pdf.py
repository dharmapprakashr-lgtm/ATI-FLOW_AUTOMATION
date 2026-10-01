"""Render the pytest-html report to PDF.

Uses the Chromium that Playwright already installs, so this adds no dependency
(no wkhtmltopdf, no weasyprint). ``page.pdf()`` is Chromium-only, which is what
the suite runs anyway.

The pytest-html 4.x report builds its table from embedded JSON at runtime and
starts with passed tests collapsed, so this waits for the table to populate and
expands every row first - otherwise the PDF captures an empty shell.

Usage::

    # standalone
    python -m utils.report_to_pdf
    python -m utils.report_to_pdf reports/report.html reports/report.pdf

    # as part of a run
    pytest --pdf-report
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HTML = ROOT_DIR / "reports" / "report.html"
DEFAULT_PDF = ROOT_DIR / "reports" / "report.pdf"

# Print-only styling: drop the interactive chrome, keep results from being split
# down the middle of a page, and force the light palette so the PDF is legible
# when the generating machine is in dark mode.
_PRINT_CSS_TEMPLATE = """
html, body {
    background: #fff !important;
    color: #000 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}
/* Interactive-only controls carry no meaning on paper. div.collapse wraps the
   show/hide buttons; hiding only the buttons leaves their "/" separator behind. */
div.collapse, .filters, #filters-container, .sortable .sort-icon {
    display: none !important;
}
/* The report lays out at ~1264px and its table will not shrink on its own.
   Constraining the body and fixing the table layout makes it reflow to the
   printable width, which keeps text at full size - scaling the whole page down
   to fit would render it at ~56%. */
html, body {
    width: __PRINTABLE__px !important;
    min-width: 0 !important;
    max-width: __PRINTABLE__px !important;
    margin: 0 !important;
}
#results-table { width: 100% !important; table-layout: fixed !important; }
td, th { word-wrap: break-word !important; overflow-wrap: anywhere !important; }
tr, .results-table-row, .log { page-break-inside: avoid; }
.log, pre {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    max-height: none !important;
    overflow: visible !important;
}
img { max-width: 100% !important; height: auto !important; page-break-inside: avoid; }
"""

#: A4 at 96 CSS px per inch.
_A4_WIDTH_PX = 794
_MARGIN_MM = 10
_MM_PER_PX = 25.4 / 96
#: Usable width once the left and right margins are removed.
_PRINTABLE_PX = int(_A4_WIDTH_PX - (2 * _MARGIN_MM / _MM_PER_PX))

# Rows render asynchronously; give the table a moment to exist before expanding.
_EXPAND_SCRIPT = """
() => {
    document.querySelectorAll('.collapsed').forEach(el => el.classList.remove('collapsed'));
    document.querySelectorAll('.extras-row, .collapsible, .log').forEach(el => {
        el.style.display = '';
        el.style.maxHeight = 'none';
        el.style.overflow = 'visible';
    });
    document.querySelectorAll('details').forEach(el => el.open = true);
    return document.querySelectorAll('tbody tr').length;
}
"""


def html_to_pdf(html_path=DEFAULT_HTML, pdf_path=DEFAULT_PDF, timeout=30000, raw=False,
                margin=None):
    """Convert an HTML report to PDF. Returns (pdf_path, row_count, scale).

    ``raw=False`` (default) targets the pytest-html report: it expands the
    collapsed rows and injects width-forcing CSS to make that report's rigid
    table reflow.

    ``raw=True`` renders the document exactly as authored. Use it for pages that
    are already designed for print - the pytest-html fixes actively damage them,
    since forcing a fixed body width clips a fluid layout.

    Raises FileNotFoundError when the report does not exist - usually because
    pytest has not been run yet, or was run with a different --html path.
    """
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if not html_path.exists():
        raise FileNotFoundError(
            f"No HTML report at {html_path}. Run pytest first (it writes "
            f"reports/report.html via pytest.ini)."
        )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        # Lay out at the printable width. documentElement.scrollWidth never
        # reports below the viewport, so a wide viewport would floor the
        # fit-to-width measurement below and force a needless scale-down.
        page = browser.new_page(viewport={"width": _PRINTABLE_PX, "height": 1123})
        try:
            page.goto(html_path.as_uri(), wait_until="networkidle", timeout=timeout)

            if raw:
                # Already print-designed: render as authored.
                page.wait_for_timeout(300)
                row_count = page.evaluate("() => document.querySelectorAll('tbody tr').length")
                scale = 1.0
            else:
                # The results table is populated by JS after load.
                try:
                    page.wait_for_selector("tbody tr", timeout=5000)
                except Exception:
                    # A report with zero results has no rows; still worth rendering.
                    pass

                row_count = page.evaluate(_EXPAND_SCRIPT)
                page.add_style_tag(
                    content=_PRINT_CSS_TEMPLATE.replace("__PRINTABLE__", str(_PRINTABLE_PX))
                )
                page.wait_for_timeout(500)

                # The report's table does not reflow below its natural width, so
                # a plain A4 render clips the rightmost column. Measure the
                # laid-out content and scale to fit rather than assuming it will
                # shrink.
                content_width = page.evaluate(
                    "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)"
                )
                printable_px = _A4_WIDTH_PX - (2 * _MARGIN_MM / _MM_PER_PX)
                scale = min(1.0, printable_px / content_width) if content_width else 1.0
                scale = max(0.1, round(scale, 3))  # Chromium accepts 0.1 - 2.0

            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                scale=scale,
                margin=margin or {"top": "12mm", "bottom": "12mm",
                                  "left": "10mm", "right": "10mm"},
                display_header_footer=True,
                header_template='<div style="font-size:8px;width:100%;padding:0 10mm;'
                                'color:#666;">AtiFlow Automation - Test Report</div>',
                footer_template='<div style="font-size:8px;width:100%;padding:0 10mm;'
                                'color:#666;text-align:right;">'
                                '<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
            )
        finally:
            browser.close()

    return pdf_path, row_count, scale


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    html_path = Path(argv[0]) if argv else DEFAULT_HTML
    pdf_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PDF

    pdf_path, row_count, scale = html_to_pdf(html_path, pdf_path)
    size_kb = pdf_path.stat().st_size / 1024
    print(f"Wrote {pdf_path} ({size_kb:.0f} KB, {row_count} result rows, scale {scale})")
    if row_count == 0:
        print(
            "Warning: the source report contains no test results. If this was a "
            "--collect-only run, re-run pytest normally and regenerate."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
