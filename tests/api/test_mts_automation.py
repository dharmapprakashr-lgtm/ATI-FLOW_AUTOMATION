"""Individually collected results from the legacy MTS model/API harnesses."""
import ast
import json
import re
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest

API_DIR = Path(__file__).resolve().parent

LEGACY_SUITES = {
    "test_mes_integration_polling.py": {"code": "mts135", "name": "mes_integration_polling", "title_index": 2},
    "test_central_config_health.py": {"code": "mts136", "name": "central_config_health", "title_index": 2},
    "test_processing_staging_grid.py": {"code": "mts146", "name": "processing_staging_grid", "title_index": 2},
    "test_material_master_config.py": {"code": "mts147", "name": "material_master_config", "title_index": 3},
    "test_settings_rest_api.py": {"code": "mts155", "name": "settings_rest_api", "title_index": 2},
    "test_tablet_login_security.py": {"code": "mts162", "name": "tablet_login_security", "title_index": 5},
    "test_external_connections_setup.py": {"code": "mts167", "name": "external_connections_setup", "title_index": 5},
}


def suite_info(path):
    try:
        return LEGACY_SUITES[path.name]
    except KeyError as exc:
        raise ValueError(f"Unknown legacy MTS runner: {path.name}") from exc


def suite_id(path):
    return suite_info(path)["code"]


def suite_name(path):
    return suite_info(path)["name"]


def _safe_literal(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return ""
    return value if isinstance(value, str) else ""


def _slug(value):
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", value).strip("_") or "case"


def case_metadata(path):
    """Discover declared cases without importing a runner or contacting servers."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = sorted(
        (
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "record"
        ),
        key=lambda node: node.lineno,
    )
    title_index = suite_info(path)["title_index"]
    cases = []
    for call in calls:
        case_id = _safe_literal(call.args[0]) if call.args else ""
        module = _safe_literal(call.args[1]) if len(call.args) > 1 else ""
        title = _safe_literal(call.args[title_index]) if len(call.args) > title_index else ""
        cases.append({
            "id": case_id,
            "module": module,
            "title": title or module or case_id,
            "pytest_id": f"{suite_name(path)}__{case_id}__{_slug(title or module)}",
        })
    ids = [case["id"] for case in cases]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError(f"Missing or duplicate case IDs in {path.name}")
    return cases


def case_ids(path):
    return [case["id"] for case in case_metadata(path)]


def run_suite(source_path, work_dir):
    """Run in a child process; process exit releases legacy server threads."""
    work_dir.mkdir(parents=True, exist_ok=True)
    # Older runners hardcode the author's home directory, including default
    # arguments evaluated at import. Adapt paths before loading the copy.
    source = source_path.read_text(encoding="utf-8")
    source = source.replace("/home/mohitkumarmishra/Desktop", str(work_dir))
    source = source.replace("/home/mohitkumarmishra/AUTOMATION", str(work_dir))
    adapted = work_dir / source_path.name
    adapted.write_text(source, encoding="utf-8")
    module = runpy.run_path(str(adapted))
    suite = suite_id(source_path)
    if suite in {"mts146", "mts147"}:
        server = module["start_local_api_server"]()
        try:
            results = module["execute_test_cases"](use_playwright=False)
        finally:
            server.shutdown()
            server.server_close()
    elif suite == "mts135":
        results = module["run_all_actual_tests"]()[0]
    else:
        results = module[f"run_all_{suite}_tests"]()
    expected = case_ids(source_path)
    actual = [result["id"] for result in results]
    if actual != expected:
        raise ValueError(f"Runner results do not match declared cases: {actual!r}")
    (work_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--run-legacy-suite":
        run_suite(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
        raise SystemExit(0)
    raise SystemExit("Usage: test_mts_automation.py --run-legacy-suite <runner> <work-dir>")


pytestmark = [pytest.mark.api, pytest.mark.api_model]
RUNNERS = [API_DIR / name for name in LEGACY_SUITES]
CASES = [
    pytest.param(path.name, case["id"], case["title"], id=case["pytest_id"])
    for path in RUNNERS for case in case_metadata(path)
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
                        [
                            sys.executable,
                            str(API_DIR / "test_mts_automation.py"),
                            "--run-legacy-suite",
                            str(API_DIR / filename),
                            str(work),
                        ],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        timeout=180,
                    )
                if process.returncode:
                    raise RuntimeError(f"Runner exited {process.returncode}")
                results = json.loads((work / "results.json").read_text(encoding="utf-8"))
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


@pytest.mark.parametrize("runner,case_id,case_title", CASES)
def test_legacy_api_case(runner, case_id, case_title, mts_results, record_property):
    result = mts_results(runner)[case_id]
    record_property("suite", suite_name(API_DIR / runner))
    record_property("case_id", case_id)
    record_property("case_title", case_title)
    record_property("execution_mode", "legacy model/mock harness; not live UI validation")
    record_property("actual_result", result.get("actual", ""))
    assert result["status"].lower() == "pass", (
        f"{runner}::{case_id} {case_title}: {result.get('actual', result)}"
    )
