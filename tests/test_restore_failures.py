"""Real PowerShell restoration with a private executable spy, never real ADB."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PWSH = os.environ.get("POWERSHELL_EXECUTABLE") or shutil.which("pwsh")
SPY = r'''
import json, os, sys
from pathlib import Path
root = Path(os.environ["ADB_SPY_ROOT"])
assert Path(sys.argv[0]).resolve() == root / "bin" / "adb"
assert os.environ["PATH"] == str(root / "bin")
args = sys.argv[1:]
with (root / "adb.jsonl").open("a") as f:
    f.write(json.dumps(args) + "\n")
# Even misleading success text must not override a native nonzero exit code.
print("Success")
if args[-1] in json.loads(os.environ["ADB_SPY_FAILURES"]): sys.exit(41)
'''


@unittest.skipUnless(PWSH, "native PowerShell unavailable; set POWERSHELL_EXECUTABLE")
class RestoreFailureTests(unittest.TestCase):
    def invoke(self, failures):
        assert PWSH is not None
        with tempfile.TemporaryDirectory(prefix="restore-result-spy-") as temp:
            root = Path(temp).resolve()
            app, tools = root / "app", root / "bin"
            app.mkdir()
            tools.mkdir()
            for name in ("restore.ps1", "package-list.ps1"):
                shutil.copyfile(ROOT / name, app / name)
            (app / "packages.txt").write_bytes(b"com.example.one\ncom.example.two\n")
            spy = tools / "adb"
            spy.write_text(f"#!{sys.executable}\n" + SPY)
            spy.chmod(0o700)
            env = {"PATH": str(tools), "HOME": str(root), "TMPDIR": str(root),
                   "ADB_SPY_ROOT": str(root), "ADB_SPY_FAILURES": json.dumps(failures),
                   "ADB_SPY_SCRIPT": str(app / "restore.ps1"), "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}
            launch = ("$env:PATH = Join-Path $env:ADB_SPY_ROOT 'bin'; "
                      "if ((Get-Command adb -CommandType Application -ErrorAction Stop).Source "
                      "-ne (Join-Path $env:PATH 'adb')) { exit 97 }; & $env:ADB_SPY_SCRIPT")
            result = subprocess.run([PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", launch],
                                    cwd=root, env=env, capture_output=True, timeout=20)
            self.assertNotEqual(result.returncode, 97, "ADB must resolve exclusively to the synthetic spy")
            records = [json.loads(line) for line in (root / "adb.jsonl").read_text().splitlines()]
            receipt_root = os.environ.get("POWERSHELL_TEST_RECEIPTS")
            if receipt_root:
                out = Path(receipt_root) / self._testMethodName / ("-".join(failures) or "success")
                out.mkdir(parents=True, exist_ok=False)
                (out / "stdout.bin").write_bytes(result.stdout)
                (out / "stderr.bin").write_bytes(result.stderr)
                (out / "adb.jsonl").write_bytes((root / "adb.jsonl").read_bytes())
                (out / "receipt.json").write_text(json.dumps({"argv": result.args, "cwd": str(root),
                    "environment": env, "exit": result.returncode, "source_sha256": {
                        n: hashlib.sha256((app / n).read_bytes()).hexdigest()
                        for n in ("restore.ps1", "package-list.ps1")}}, indent=2) + "\n")
            self.assertEqual(records, [
                ["shell", "cmd", "package", "install-existing", "com.example.one"],
                ["shell", "cmd", "package", "install-existing", "com.example.two"],
                ["shell", "pm", "enable", "com.samsung.android.game.gos"]])
            return result

    def test_failed_restores_are_reported_without_hiding_later_results(self):
        for failures in (["com.example.one"], ["com.samsung.android.game.gos"],
                         ["com.example.one", "com.samsung.android.game.gos"]):
            with self.subTest(failures=failures):
                result = self.invoke(failures)
                self.assertNotEqual(result.returncode, 0, "failed native restores must not exit successfully")
                self.assertEqual(result.stdout.count(b"[FAILED]"), len(failures))
                self.assertEqual(result.stdout.count(b"[OK]"), 3 - len(failures))
                self.assertIn(b"[ERROR]", result.stdout)
                self.assertNotIn(b"[DONE]", result.stdout)
                self.assertNotIn(b"All packages successfully restored", result.stdout)

    def test_all_successful_commands_keep_success_message_and_zero_status(self):
        result = self.invoke([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count(b"[OK]"), 3)
        self.assertIn(b"[DONE] All packages successfully restored!", result.stdout)
        self.assertNotIn(b"[FAILED]", result.stdout)


if __name__ == "__main__":
    unittest.main()
