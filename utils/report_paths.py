"""Where this run's artifacts go.

``reports/`` holds **only** finished PDF reports, one per run, named by start
time so runs accumulate instead of overwriting each other::

    reports/
    ├── report_2026-08-12_10-29-27.pdf
    ├── report_2026-08-12_10-30-37.pdf
    └── report_2026-08-12_11-02-07.pdf

The timestamp format sorts lexicographically in chronological order, so a plain
directory listing is already in run order and the newest run is last.

Everything needed to *build* that PDF - failure screenshots, the summary HTML it
is rendered from - is intermediate. It goes to a temporary directory outside the
project and is deleted once the PDF is written; the screenshots survive inside
the PDF as embedded images. Nothing but PDFs is ever created in ``reports/``.

``RUN_STAMP`` and ``WORK_DIR`` are computed once at import. Both conftests and
the report builders import this module, so they agree on one destination for the
whole session even though they run at different points in the pytest lifecycle.

Old reports are pruned to the newest ``REPORT_KEEP_RUNS`` (default 20) at the
end of each session; set it to 0 to keep everything.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT_DIR / "reports"

RUN_STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
PDF_PREFIX = "report_"


def _unique_pdf_path():
    """Return an unused report path.

    Two sessions starting in the same second (parallel CI jobs) would otherwise
    write to the same file.
    """
    stamp = datetime.now().strftime(RUN_STAMP_FORMAT)
    candidate = REPORTS_DIR / f"{PDF_PREFIX}{stamp}.pdf"
    suffix = 2
    while candidate.exists():
        candidate = REPORTS_DIR / f"{PDF_PREFIX}{stamp}_{suffix}.pdf"
        suffix += 1
    return candidate, stamp


PDF_PATH, RUN_STAMP = _unique_pdf_path()

#: Scratch space for this run, outside the project so reports/ stays clean.
#: Created lazily by ensure_work_dir() and removed by cleanup_work_dir().
WORK_DIR = Path(tempfile.gettempdir()) / f"atiflow_run_{RUN_STAMP}"
SCREENSHOT_DIR = WORK_DIR / "screenshots"
SUMMARY_HTML_PATH = WORK_DIR / "report_summary.html"
HTML_PATH = WORK_DIR / "report.html"


def keep_runs():
    """How many PDF reports to retain. 0 means keep everything."""
    try:
        return max(0, int(os.environ.get("REPORT_KEEP_RUNS", "20")))
    except ValueError:
        return 20


def ensure_dirs():
    """Create reports/ and this run's scratch space. Safe to call repeatedly."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return WORK_DIR


def cleanup_work_dir():
    """Delete this run's scratch space once the PDF has been written."""
    shutil.rmtree(WORK_DIR, ignore_errors=True)


def list_reports():
    """Every PDF report, oldest first."""
    if not REPORTS_DIR.exists():
        return []
    return sorted(REPORTS_DIR.glob(f"{PDF_PREFIX}*.pdf"), key=lambda p: p.name)


def prune_old_reports(keep=None):
    """Delete all but the newest ``keep`` PDF reports. Returns the count."""
    keep = keep_runs() if keep is None else keep
    if keep <= 0:
        return 0

    removed = 0
    for stale in list_reports()[:-keep]:
        try:
            stale.unlink()
            removed += 1
        except OSError:
            pass
    return removed
