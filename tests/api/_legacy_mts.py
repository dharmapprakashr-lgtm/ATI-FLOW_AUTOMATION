"""Bridge legacy stateful MTS runners to pytest without import-time execution."""
import ast
import json
from pathlib import Path
import runpy
import sys

API_DIR = Path(__file__).resolve().parent


def case_ids(path):
    """Discover declared cases without importing a runner or contacting servers."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = sorted(
        (node for node in ast.walk(tree)
         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
         and node.func.id == "record"),
        key=lambda node: node.lineno,
    )
    ids = [ast.literal_eval(call.args[0]) for call in calls]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError(f"Missing or duplicate case IDs in {path.name}")
    return ids


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
    suite = source_path.stem.split("_")[1]
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
    run_suite(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
