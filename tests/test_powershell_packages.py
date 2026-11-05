"""Run real PowerShell scripts with an isolated executable ADB spy, never a device.

Set POWERSHELL_EXECUTABLE to pwsh (PowerShell 7+) or a compatible executable.
When unavailable these native controls explicitly skip, not source-only passes.
"""
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
root = Path(os.environ["ADB_SPY_ROOT"]).resolve()
assert Path(sys.argv[0]).resolve() == root / "bin" / "adb"
assert os.environ["PATH"] == str(root / "bin")
with (root / "adb.jsonl").open("a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "executable": str(Path(sys.argv[0]).resolve())}) + "\n")
if sys.argv[1:] == ["get-state"]:
    if os.environ.get("ADB_SPY_OFFLINE") == "1": sys.exit(1)
    print("device")
else:
    print("Success")
'''


@unittest.skipUnless(PWSH, "native PowerShell unavailable; set POWERSHELL_EXECUTABLE")
class PowerShellPackagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="powershell-package-spy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.app = self.root / "app"
        self.app.mkdir()
        for file in ROOT.glob("*.ps1"):
            shutil.copyfile(file, self.app / file.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.spy = self.bin / "adb"
        self.spy.write_text(f"#!{sys.executable}\n" + SPY)
        self.spy.chmod(0o700)
        self.log = self.root / "adb.jsonl"
        self.canary = self.root / "PWNED"
        self.canary.write_bytes(b"protected synthetic canary\n")
        self.runs = 0

    def run_script(self, name, data, **flags):
        self.runs += 1
        self.log.unlink(missing_ok=True)
        packages = self.app / "packages.txt"
        if data is None:
            packages.unlink(missing_ok=True)
        else:
            packages.write_bytes(data)
        env = {"PATH": str(self.bin), "HOME": str(self.root), "TMPDIR": str(self.root),
               "ADB_SPY_ROOT": str(self.root), "ADB_SPY_BIN": str(self.bin),
               "ADB_SPY_SCRIPT": str(self.app / name), "DOTNET_CLI_TELEMETRY_OPTOUT": "1", **flags}
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.app.glob("*.ps1")}
        # PowerShell prepends PSHOME to PATH on startup. Reset it inside the
        # process and prove command resolution before invoking untouched source.
        launch = ("$env:PATH = $env:ADB_SPY_BIN; "
                  "if ((Get-Command adb -CommandType Application -ErrorAction Stop).Source "
                  "-ne (Join-Path $env:ADB_SPY_BIN 'adb')) { exit 97 }; & $env:ADB_SPY_SCRIPT")
        assert PWSH is not None
        result = subprocess.run([PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", launch],
                                cwd=self.root, env=env, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 97, "ADB must resolve only to the private executable spy")
        records = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        target = os.environ.get("POWERSHELL_TEST_RECEIPTS")
        if target:
            out = Path(target) / self._testMethodName / f"{self.runs:02d}-{name}"
            out.mkdir(parents=True, exist_ok=False)
            (out / "stdout.bin").write_bytes(result.stdout)
            (out / "stderr.bin").write_bytes(result.stderr)
            (out / "adb.jsonl").write_bytes(self.log.read_bytes() if self.log.exists() else b"")
            (out / "receipt.json").write_text(json.dumps({"argv": result.args, "exit": result.returncode,
                "cwd": str(self.root), "environment": env, "source_sha256": before}, indent=2) + "\n")
            if data is not None: (out / "packages.bin").write_bytes(data)
        self.assertEqual(self.canary.read_bytes(), b"protected synthetic canary\n")
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.app.glob("*.ps1")})
        if data is not None: self.assertEqual(packages.read_bytes(), data)
        for record in records: self.assertEqual(record["executable"], str(self.spy))
        return result, [r["argv"] for r in records]

    def expected(self, script, packages):
        if script == "debloat.ps1":
            return [["get-state"]] + [["shell", "pm", "uninstall", "-k", "--user", "0", p] for p in packages] + [
                ["shell", "pm", "disable-user", "--user", "0", "com.samsung.android.game.gos"]]
        return [["shell", "cmd", "package", "install-existing", p] for p in packages] + [
            ["shell", "pm", "enable", "com.samsung.android.game.gos"]]

    def test_late_invalid_identifier_refuses_before_any_adb(self):
        for script in ["debloat.ps1", "restore.ps1"]:
            for bad in [b"--user", b"com..example", b"com.2bad", b"com.example two", b"com.example#inline",
                        b"com.example; touch PWNED", b"$(touch PWNED)", b"com.example\x00bad", b"com.example\rbad",
                        "com.exémple.app".encode(), "com.example.Δelta".encode()]:
                with self.subTest(script=script, bad=bad):
                    result, calls = self.run_script(script, b"com.example.valid\n" + bad + b"\ncom.example.last\n")
                    self.assertEqual(calls, [], "entire package list must validate before any ADB call")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b"[ERROR]", result.stdout + result.stderr)
                    self.assertNotIn(b"[DONE]", result.stdout)

    def test_crlf_comments_whitespace_final_line_case_order_duplicates(self):
        data = b"  # comment\r\n\t\r\n com.example.First_2\t\r\nandroid\r\ncom.example.First_2\r\n\tunknown_pkg \t"
        expected = ["com.example.First_2", "android", "com.example.First_2", "unknown_pkg"]
        for script in ["debloat.ps1", "restore.ps1"]:
            with self.subTest(script=script):
                result, calls = self.run_script(script, data)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, self.expected(script, expected))
                self.assertIn(b"[DONE]", result.stdout)

    def test_single_record_and_empty_lists_keep_gos_action(self):
        for script in ["debloat.ps1", "restore.ps1"]:
            for data, expected in [(b"com.example.one", ["com.example.one"]), (b"", []), (b" \t\r\n # comment\n", [])]:
                with self.subTest(script=script, data=data):
                    result, calls = self.run_script(script, data)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(calls, self.expected(script, expected))

    def test_missing_file_refuses_before_adb(self):
        for script in ["debloat.ps1", "restore.ps1"]:
            with self.subTest(script=script):
                result, calls = self.run_script(script, None)
                self.assertEqual(calls, [])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"packages.txt", result.stdout + result.stderr)
                self.assertNotIn(b"[DONE]", result.stdout)

    def test_debloat_offline_still_stops_before_uninstall(self):
        result, calls = self.run_script("debloat.ps1", b"com.example.one\n", ADB_SPY_OFFLINE="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [["get-state"]])
        self.assertNotIn(b"[DONE]", result.stdout)


if __name__ == "__main__":
    unittest.main()
