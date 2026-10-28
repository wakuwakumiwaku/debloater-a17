import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get("DEBLOAT_SCRIPT", REPO / "debloat.sh")).resolve()
INVENTORY = (REPO / "packages.txt").read_bytes()


def require_tool(name):
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Required test tool not found: {name}")
    return path


BASH = require_tool("bash")
DIRNAME = require_tool("dirname")
GOS = ["shell", "pm", "disable-user", "--user", "0", "com.samsung.android.game.gos"]
SPY = r'''import json
import os
from pathlib import Path
import sys

root = Path(os.environ["ADB_SPY_ROOT"]).resolve()
executable = Path(__file__).resolve()
log = Path(os.environ["ADB_SPY_LOG"]).resolve()
if executable != root / "bin" / "adb" or log != root / "adb.jsonl":
    raise SystemExit("spy ownership assertion failed")
if os.environ["PATH"] != str(root / "bin"):
    raise SystemExit("spy PATH assertion failed")
args = sys.argv[1:]
with log.open("a") as stream:
    stream.write(json.dumps({"argv": args, "executable": str(executable), "path": os.environ["PATH"],
                             "lc_all": os.environ.get("LC_ALL"), "locpath": os.environ.get("LOCPATH")}) + "\n")
if args == ["get-state"]:
    print("device")
    raise SystemExit(int(os.environ.get("ADB_SPY_OFFLINE", "0")))
if args[:6] == ["shell", "pm", "uninstall", "-k", "--user", "0"] and len(args) == 7:
    raise SystemExit(int(args[-1] == os.environ.get("ADB_SPY_SKIP")))
if args == ["shell", "pm", "disable-user", "--user", "0", "com.samsung.android.game.gos"]:
    raise SystemExit(0)
raise SystemExit("unexpected adb command")
'''


class DebloatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="debloat-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.app = self.root / "app"
        self.app.mkdir()
        self.script = self.app / "debloat.sh"
        self.script.write_bytes(SCRIPT.read_bytes())
        self.packages = self.app / "packages.txt"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.spy = self.bin / "adb"
        self.spy.write_text(f"#!{sys.executable}\n" + SPY)
        self.spy.chmod(0o700)
        (self.bin / "dirname").symlink_to(DIRNAME)
        self.log = self.root / "adb.jsonl"
        self.canary = self.root / "canary"
        self.canary.write_bytes(b"do not change\n")
        # No system PATH: real adb cannot be selected even if installed on the host.
        self.env = {
            "PATH": str(self.bin), "LC_ALL": "C",
            "ADB_SPY_ROOT": str(self.root), "ADB_SPY_LOG": str(self.log),
        }
        for key in ("HOME", "TMPDIR"):
            directory = self.root / key.lower()
            directory.mkdir()
            self.env[key] = str(directory)
        self.run_number = 0

    def retain_run(self, kind, result, env, data=None):
        target = os.environ.get("DEBLOAT_TEST_RECEIPTS")
        if not target:
            return
        self.run_number += 1
        directory = Path(target) / self._testMethodName / f"{self.run_number:02d}-{kind}"
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "stdout.bin").write_bytes(result.stdout)
        (directory / "stderr.bin").write_bytes(result.stderr)
        (directory / "adb.jsonl").write_bytes(self.log.read_bytes() if self.log.exists() else b"")
        if data is not None:
            (directory / "packages.bin").write_bytes(data)
        (directory / "receipt.json").write_text(json.dumps({
            "argv": result.args, "env": env, "cwd": str(self.root), "exit": result.returncode,
            "script_source": str(SCRIPT), "script_sha256": hashlib.sha256(self.script.read_bytes()).hexdigest(),
        }, indent=2) + "\n")

    def non_c_locale_flags(self):
        name = os.environ.get("DEBLOAT_TEST_LOCALE")
        if not name or name.split(".")[0].upper() in ("C", "POSIX"):
            self.skipTest("set DEBLOAT_TEST_LOCALE to an available non-C collating locale")
        flags = {"LC_ALL": name}
        if "LOCPATH" in os.environ:
            flags["LOCPATH"] = os.environ["LOCPATH"]
        env = dict(self.env, **flags)
        probe = subprocess.run(
            [sys.executable, "-c", 'import locale; print(locale.setlocale(locale.LC_ALL, ""))'],
            cwd=self.root, env=env, capture_output=True, timeout=15,
        )
        self.retain_run("locale-probe", probe, env)
        if probe.returncode != 0:
            self.skipTest(f"non-C locale {name!r} unavailable: {probe.stderr!r}")
        self.assertTrue(probe.stdout.strip(), "locale availability probe returned no locale")
        return flags

    def run_script(self, data, **flags):
        if self.log.exists():
            self.log.unlink()
        if data is None:
            if self.packages.exists():
                self.packages.unlink()
        else:
            self.packages.write_bytes(data)
        env = dict(self.env, **flags)
        result = subprocess.run(
            [BASH, "-c", '[[ "$(command -v adb)" == "$1" ]] || exit 97; exec "$2" "$3"',
             "spy-check", str(self.spy), BASH, str(self.script)],
            cwd=self.root, env=env, capture_output=True, timeout=15,
        )
        self.retain_run("script", result, env, data)
        self.assertNotEqual(result.returncode, 97, "adb did not resolve to the owned spy")
        records = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        for record in records:
            self.assertEqual(record["executable"], str(self.spy))
            self.assertEqual(record["path"], str(self.bin))
            self.assertEqual(record["lc_all"], env["LC_ALL"])
            self.assertEqual(record["locpath"], env.get("LOCPATH"))
        self.assertEqual(self.canary.read_bytes(), b"do not change\n")
        self.assertEqual(self.script.read_bytes(), SCRIPT.read_bytes())
        if data is not None:
            self.assertEqual(self.packages.read_bytes(), data)
        self.assertFalse((self.root / "PWNED").exists())
        self.assertFalse((self.app / "PWNED").exists())
        return result, [record["argv"] for record in records]

    def expected_calls(self, packages):
        return [["get-state"]] + [
            ["shell", "pm", "uninstall", "-k", "--user", "0", pkg] for pkg in packages
        ] + [GOS]

    def assert_success(self, data, packages, **flags):
        result, calls = self.run_script(data, **flags)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, self.expected_calls(packages))
        self.assertIn(b"[DONE]", result.stdout)

    def test_unchanged_lf_inventory_exact_arguments_and_order(self):
        packages = [line for line in INVENTORY.decode().splitlines() if line and not line.startswith("#")]
        self.assertTrue(packages)
        self.assert_success(INVENTORY, packages)

    def test_crlf_whitespace_blank_lines_and_indented_comments(self):
        self.assert_success(
            b"  # Windows-edited list\r\n\t\r\n  com.example.first \t\r\n"
            b"\t# comment\t\r\n\tcom.example.Second_2\t\r\n\r\n",
            ["com.example.first", "com.example.Second_2"],
        )

    def test_lf_edge_whitespace(self):
        self.assert_success(b"\tcom.example.one \t\n  # note\n \t\n", ["com.example.one"])

    def test_final_line_without_newline(self):
        self.assert_success(b"com.example.one\n \tcom.example.last \t\r", ["com.example.one", "com.example.last"])

    def test_empty_list_keeps_existing_gos_control(self):
        self.assert_success(b"", [])
        self.assert_success(b" \t\r\n  # only comments\r\n\t\r\n", [])

    def test_case_duplicates_and_order_are_not_changed(self):
        self.assert_success(
            b"com.example.Zed\ncom.example.alpha\ncom.example.Zed\nandroid\n",
            ["com.example.Zed", "com.example.alpha", "com.example.Zed", "android"],
        )

    def test_non_c_locale_ascii_identifiers_preserve_arguments_and_locale(self):
        flags = self.non_c_locale_flags()
        packages = ["Com.Example.App_09", "android", "unknown_pkg", "a0_Z.B9_c", "Com.Example.App_09"]
        data = "  # accented comment: é\r\n\t\r\n".encode() + b"".join(
            b" \t" + package.encode() + b"\t \r\n" for package in packages
        )
        self.assert_success(data, packages, **flags)

    def test_non_c_locale_late_non_ascii_rejects_before_any_adb(self):
        flags = self.non_c_locale_flags()
        for record in ["com.exémple.app", "Éxample.app", "com.example.app١", "com.example.Δelta"]:
            with self.subTest(record=record):
                data = b"com.example.Valid_1\n" + record.encode() + b"\nunknown_pkg\n"
                result, calls = self.run_script(data, **flags)
                self.assertEqual(calls, [], "non-ASCII record reached the ADB spy")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"line 2", result.stderr)
                self.assertNotIn(b"[DONE]", result.stdout)

    def test_late_malformed_records_reject_before_any_adb(self):
        malformed = [
            b"--user", b"-com.example", b"com..example", b".com.example", b"com.example.",
            b"com.example two", b"com.example\ttwo", b"com.example#inline", b"com.example # note",
            b"com.example/other", b"com.2bad", b"com.example\rjunk", b"com.example\r\r",
            b"com.example\x0bjunk", b"com.example\x1b", b"\xef\xbb\xbfcom.example",
        ]
        for record in malformed:
            with self.subTest(record=record):
                result, calls = self.run_script(b"com.example.valid\n" + record + b"\ncom.example.later\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertIn(b"line 2", result.stderr)
                self.assertNotIn(b"[DONE]", result.stdout)

    def test_shell_syntax_is_rejected_without_expansion_or_adb(self):
        for record in [
            b"com.example;touch PWNED", b"$(touch PWNED)", b"`touch PWNED`",
            b"com.example && touch PWNED", b"com.example'", b'com.example"', b"com.example*",
        ]:
            with self.subTest(record=record):
                result, calls = self.run_script(b"com.example.valid\n" + record + b"\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertIn(b"line 2", result.stderr)

    def test_nul_is_not_silently_removed_by_bash_read(self):
        result, calls = self.run_script(b"com.example.valid\ncom.exam\0ple.invalid\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn(b"[ERROR]", result.stderr)

    def test_missing_list_does_not_call_adb(self):
        result, calls = self.run_script(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn(b"packages.txt not found", result.stdout + result.stderr)

    def test_offline_device_retains_detection_failure(self):
        result, calls = self.run_script(b"com.example.one\n", ADB_SPY_OFFLINE="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [["get-state"]])
        self.assertIn(b"No ADB device detected", result.stdout)
        self.assertNotIn(b"[DONE]", result.stdout)

    def test_uninstall_failure_still_skips_and_continues(self):
        packages = ["com.example.first", "com.example.last"]
        result, calls = self.run_script("\n".join(packages).encode(), ADB_SPY_SKIP=packages[0])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, self.expected_calls(packages))
        self.assertIn(b"[SKIPPED]", result.stdout)
        self.assertIn(b"[DONE]", result.stdout)


if __name__ == "__main__":
    unittest.main()
