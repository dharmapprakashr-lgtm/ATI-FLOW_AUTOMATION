"""Individually collected results from the legacy MTS model/API harnesses."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from _legacy_mts import API_DIR, case_ids

pytestmark = [pytest.mark.api, pytest.mark.api_model]
RUNNERS = sorted(API_DIR.glob("run_mts*_automation_tests.py"))
CASES = [
    pytest.param(path.name, case_id, id=f"{path.stem.split('_')[1]}-{case_id}")
    for path in RUNNERS for case_id in case_ids(path)
]


@pytest.fixture(scope="module")
def mts_results(tmp_path_factory):
    """Cache one ordered execution per suite, with separate scratch directories."""
    cache = {}
    work_dirs = []

    def load(filename):
        if filename not in cache:
            work = tmp_path_factory.mktemp(Path(filename).stem)
            work_dirs.append(work)
            log_path = work / "execution.log"
            try:
                with log_path.open("w", encoding="utf-8") as log:
                    process = subprocess.run(
                        [sys.executable, str(API_DIR / "_legacy_mts.py"),
                         str(API_DIR / filename), str(work)],
                        stdout=log, stderr=subprocess.STDOUT, timeout=180,
                    )
                if process.returncode:
                    raise RuntimeError(f"Runner exited {process.returncode}")
                results = json.loads((work / "results.json").read_text())
                cache[filename] = {row["id"]: row for row in results}
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                cache[filename] = f"{exc}. Execution log: {log_path}"
        result = cache[filename]
        if isinstance(result, str):
            pytest.fail(result, pytrace=False)
        return result

    yield load
    for work in work_dirs:
        shutil.rmtree(work)


@pytest.mark.parametrize("runner,case_id", CASES)
def test_mts_case(runner, case_id, mts_results, record_property):
    result = mts_results(runner)[case_id]
    record_property("execution_mode", "legacy model/mock harness; not live UI validation")
    record_property("actual_result", result.get("actual", ""))
    assert result["status"].lower() == "pass", (
        f"{runner}::{case_id}: {result.get('actual', result)}"
    )
