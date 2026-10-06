"""Harness regressions; no provider calls. Runtime integration supplied by the Rust test."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import python_boundary as bench


class HarnessTests(unittest.TestCase):
    def test_generation_requires_explicit_model_and_disables_fallback(self):
        import ai_generation as generation
        with patch.object(generation, "run") as run, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                generation.main(["--cott", "cott", "--output", "unused.json"])
            run.assert_not_called()
        model = "fixture-provider/explicit-model"  # test data, never a provider invocation
        command = generation.cott_generate_command("cott", "project", model, 1)
        self.assertEqual(command[command.index("--model") + 1], model)
        with patch.object(generation, "run", return_value={"ok": True}) as run:
            generation.configure_state("omp", Path("unused-state"), model, "high")
        configurations = {call.args[0][3]: call.args[0][4] for call in run.call_args_list}
        self.assertEqual(configurations["retry.modelFallback"], "false")
        self.assertEqual(json.loads(configurations["modelRoles"])["default"], model + ":high")
        wrong = json.dumps({"type": "message_end", "message": {"role": "assistant", "provider": "other", "model": "other", "usage": {}}})
        self.assertFalse(generation.direct_usage(wrong, model)["ok"])

    def test_comparison_rejects_mixed_scope_interpreter_and_harness(self):
        import copy
        from compare_python_boundary import compare
        sample = {"status": "measured", "scope": "component", "identity": {
            "python": {"sha256": "one", "version": "v", "platform": "host"},
            "scripts": {"python_boundary.py": {"sha256": "script"}}}, "rows": []}
        for change in ("scope", "python", "script"):
            other = copy.deepcopy(sample)
            if change == "scope":
                other["scope"] = "facade"
            elif change == "python":
                other["identity"]["python"]["version"] = "another"
            else:
                other["identity"]["scripts"]["python_boundary.py"]["sha256"] = "changed"
            with self.assertRaisesRegex(ValueError, {"scope": "scopes", "python": "interpreter", "script": "harness"}[change]):
                compare(sample, other)

    def test_summary_keeps_raw_and_variation(self):
        result = bench.summary([3, 1, 2])
        self.assertEqual(result["samples"], [3, 1, 2])
        self.assertEqual((result["min"], result["median"], result["max"]), (1, 2, 3))
        self.assertEqual(result["stdev"], 1)

    def test_scopes_limits_and_history_are_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "report.json"
            base = ["--output", str(out), "--component-runtime", temp]
            with contextlib.redirect_stderr(io.StringIO()):
                for extra in (["--cott", "cott"], ["--repeat", "0"], ["--depths", "65"]):
                    with self.assertRaises(SystemExit):
                        bench.parse_args(base + extra)
                out.write_text("historical")
                with self.assertRaises(SystemExit):
                    bench.parse_args(base)
            self.assertEqual(out.read_text(), "historical")

    def test_fixture_uses_same_algorithm_and_real_interpreter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            bench.write_fixture(root, 3, "test-only", "deliberately-absent-checker")
            manifest = tomllib.loads((root / "cott.toml").read_text())
            interpreter = root / manifest["target"]["python"]["interpreter"]
            self.assertEqual(interpreter.resolve(), Path(sys.executable).resolve())
            self.assertIn("List[List[List[I32]]]", (root / "src/bench.cott").read_text())
            self.assertIn("return items", (root / "python/cott_bindings/algorithm.py").read_text())

    @unittest.skipUnless(os.environ.get("COTT_BENCH_COTT"), "compiler not supplied")
    def test_emitted_predicates_match_direct_checker_without_claiming_provenance(self):
        # Pure wrapper semantics test. The support script explicitly stubs ONLY the loader
        # in memory. Never call measure() or claim native certification for this test.
        with tempfile.TemporaryDirectory() as temp:
            for depth in (1, 3):
                for mode in bench.MODES:
                    root = Path(temp) / f"{mode}-{depth}"
                    bench.write_fixture(root, depth, mode, "deliberately-absent-checker")
                    emitted = subprocess.run([os.environ["COTT_BENCH_COTT"], "emit", "python", "--project", str(root)],
                                             capture_output=True, text=True, timeout=30)
                    self.assertEqual(emitted.returncode, 0, emitted.stderr)
                    tested = subprocess.run([sys.executable, str(bench.ROOT / "tests/support/benchmark_parity.py"),
                                             str(root), mode, str(depth)], capture_output=True, text=True, timeout=30,
                                            env=bench.environment())
                    self.assertEqual(tested.returncode, 0, tested.stderr)


    def test_failed_verify_never_runs_worker_or_claims_certificate(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "result.json"
            calls = []
            def run(argv, cwd=None):
                calls.append(argv)
                if argv[0] == "git":
                    return {"stdout": "test-head", "returncode": 0}
                return {"argv": argv, "returncode": 4 if "verify" in argv else 0,
                        "seconds": 0.1, "stderr": "test-only simulated failure"}
            with patch.object(bench, "tool_run", side_effect=run), patch.object(bench, "measure") as measure:
                code = bench.main(["--cott", sys.executable, "--output", str(out), "--depths", "1"])
            self.assertEqual(code, 1)
            measure.assert_not_called()
            report = json.loads(out.read_text())
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["rows"], [])
            self.assertEqual(report["blockers"][0]["stage"], "verify")
            self.assertIsNone(report["identity"]["model"])
            self.assertFalse(any("generate" in c for c in calls))

    def test_cold_is_separate_from_warm_work(self):
        def run(argv):
            config = json.loads(argv[-1])
            return {"returncode": 0, "seconds": 1 if config.get("phase") == "cold" else 999,
                    "stdout": json.dumps({k: 2 for k in ("setup_ns", "first_call_ns", "warm_ns_per_call",
                        "traced_peak_bytes", "traced_retained_bytes")})}
        with patch.object(bench, "tool_run", side_effect=run):
            result = bench.measure({"size": 1, "depth": 1, "arm": "direct-checked"}, 2)
        self.assertEqual(result["summary"]["cold_process_seconds"]["samples"], [1, 1])
        self.assertEqual(result["provenance"], "none")

    @unittest.skipUnless(os.environ.get("COTT_BENCH_RUNTIME"), "compiler-rendered runtime not supplied")
    def test_native_worker_modes_nesting_correctness_and_memory(self):
        runtime = os.environ["COTT_BENCH_RUNTIME"]
        for depth in (1, 3):
            for mode, context in (("boundary", False), ("test-only", False), ("test-only", True), ("off", False)):
                for arm in bench.ARMS[:2]:
                    config = {"runtime": runtime, "project": None, "mode": mode, "test_context": context,
                              "size": 3, "depth": depth, "arm": arm, "loops": 2}
                    done = subprocess.run([sys.executable, bench.__file__, "--worker", json.dumps(config)],
                                          capture_output=True, text=True, env=bench.environment())
                    self.assertEqual(done.returncode, 0, done.stderr)
                    result = json.loads(done.stdout)
                    self.assertTrue(result["correctness"]["valid_equal"])
                    expected = None if arm == "direct-unchecked" else mode == "boundary" or (mode == "test-only" and context)
                    self.assertEqual(result["correctness"]["invalid_rejected"], expected)
                    self.assertGreaterEqual(result["traced_peak_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
