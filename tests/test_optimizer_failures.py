"""Native PowerShell optimizer outcomes, with executable-only synthetic ADB."""
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
COMMANDS = [['get-state'], ['shell', 'settings', 'put', 'global', 'ram_expand_size', '0'], ['shell', 'settings', 'put', 'global', 'window_animation_scale', '0.5'], ['shell', 'settings', 'put', 'global', 'transition_animation_scale', '0.5'], ['shell', 'settings', 'put', 'global', 'animator_duration_scale', '0.5'], ['shell', 'settings', 'put', 'global', 'private_dns_mode', 'hostname'], ['shell', 'settings', 'put', 'global', 'private_dns_specifier', 'dns.adguard-dns.com'], ['shell', 'settings', 'put', 'secure', 'show_clip_access_notification', '1'], ['shell', 'settings', 'put', 'global', 'send_action_app_error', '0'], ['shell', 'settings', 'put', 'global', 'protect_battery', '3'], ['shell', 'logcat', '-G', '64K']]
SPY = r'''import json, os, sys
from pathlib import Path
root = Path(os.environ["ADB_SPY_ROOT"]).resolve()
assert Path(sys.argv[0]).resolve() == root / "bin" / "adb"
assert os.environ["PATH"] == str(root / "bin")
args = sys.argv[1:]
assert args in json.loads(os.environ["ADB_SPY_COMMANDS"])
log = root / "adb.jsonl"
index = len(log.read_text().splitlines()) if log.exists() else 0
with log.open("a") as f: f.write(json.dumps(args) + "\n")
print("Success")  # Native failure status must win over optimistic stdout.
if index == int(os.environ["ADB_SPY_FAIL_INDEX"]): sys.exit(41)
'''


@unittest.skipUnless(PWSH, "native PowerShell unavailable; set POWERSHELL_EXECUTABLE")
class OptimizerFailureTests(unittest.TestCase):
    def invoke(self, fail_index):
        assert PWSH is not None
        with tempfile.TemporaryDirectory(prefix="optimizer-spy-") as temp:
            root = Path(temp).resolve()
            tools = root / "bin"
            tools.mkdir()
            script = root / "optimize.ps1"
            script.write_bytes((ROOT / "optimize.ps1").read_bytes())
            spy = tools / "adb"
            spy.write_text(f"#!{sys.executable}\n" + SPY)
            spy.chmod(0o700)
            canary = root / "canary"
            canary.write_bytes(b"synthetic protected input")
            env = {"PATH": str(tools), "HOME": str(root), "TMPDIR": str(root),
                   "XDG_CACHE_HOME": str(root / "cache"), "XDG_CONFIG_HOME": str(root / "config"),
                   "ADB_SPY_ROOT": str(root), "ADB_SPY_COMMANDS": json.dumps(COMMANDS),
                   "ADB_SPY_FAIL_INDEX": str(fail_index), "ADB_SPY_SCRIPT": str(script),
                   "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "POWERSHELL_TELEMETRY_OPTOUT": "1"}
            launch = ("$env:PATH = Join-Path $env:ADB_SPY_ROOT 'bin'; "
                      "if ((Get-Command adb -CommandType Application -ErrorAction Stop).Source "
                      "-ne (Join-Path $env:PATH 'adb')) { exit 97 }; & $env:ADB_SPY_SCRIPT")
            result = subprocess.run([PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", launch],
                                    cwd=root, env=env, capture_output=True, timeout=20)
            self.assertNotEqual(result.returncode, 97, "ADB must resolve only to the owned executable spy")
            log = root / "adb.jsonl"
            records = [json.loads(line) for line in log.read_text().splitlines()]
            receipts = os.environ.get("OPTIMIZER_TEST_RECEIPTS")
            if receipts:
                out = Path(receipts) / self._testMethodName / str(fail_index)
                out.mkdir(parents=True, exist_ok=False)
                (out / "stdout.bin").write_bytes(result.stdout)
                (out / "stderr.bin").write_bytes(result.stderr)
                (out / "adb.jsonl").write_bytes(log.read_bytes())
                (out / "receipt.json").write_text(json.dumps({"argv": result.args, "cwd": str(root),
                    "environment": env, "exit": result.returncode, "timeout_seconds": 20,
                    "source_sha256": hashlib.sha256(script.read_bytes()).hexdigest()}, indent=2) + "\n")
            self.assertEqual(script.read_bytes(), (ROOT / "optimize.ps1").read_bytes())
            self.assertEqual(canary.read_bytes(), b"synthetic protected input")
            return result, records

    def test_every_failed_optimization_stops_before_later_commands_and_success_summary(self):
        for index in range(1, len(COMMANDS)):
            with self.subTest(index=index, command=COMMANDS[index]):
                result, calls = self.invoke(index)
                self.assertNotEqual(result.returncode, 0, "failed optimization must not exit successfully")
                self.assertEqual(calls, COMMANDS[:index + 1], "stop after the failed operation")
                self.assertIn(b"[ERROR]", result.stdout + result.stderr)
                self.assertNotIn(b"[DONE]", result.stdout)

    def test_all_successful_commands_keep_original_arguments_order_and_summary(self):
        result, calls = self.invoke(-1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, COMMANDS)
        self.assertIn(b"[DONE] All optimizations applied successfully!", result.stdout)
        self.assertNotIn(b"[ERROR]", result.stdout + result.stderr)

    def test_detection_failure_does_not_attempt_optimization(self):
        result, calls = self.invoke(0)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, COMMANDS[:1])
        self.assertNotIn(b"[DONE]", result.stdout)


if __name__ == "__main__":
    unittest.main()
