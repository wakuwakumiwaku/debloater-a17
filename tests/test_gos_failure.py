"""A failed GOS restriction is not a completed debloat run, offline only."""
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
BASH = shutil.which("bash")
DIRNAME = shutil.which("dirname")
GOS = ["shell", "pm", "disable-user", "--user", "0", "com.samsung.android.game.gos"]
EXPECTED = [["get-state"], ["shell", "pm", "uninstall", "-k", "--user", "0", "com.example.synthetic"], GOS]
SPY = r'''import json, os, sys
from pathlib import Path
root = Path(os.environ["ADB_SPY_ROOT"]).resolve()
assert Path(sys.argv[0]).resolve() == root / "bin" / "adb"
assert os.environ["PATH"] == str(root / "bin")
args = sys.argv[1:]
assert args in json.loads(os.environ["ADB_SPY_EXPECTED"])
with (root / "adb.jsonl").open("a") as f: f.write(json.dumps(args) + "\n")
print("Success")
if "disable-user" in args and os.environ["ADB_SPY_FAIL_GOS"] == "1": sys.exit(49)
'''


class GosFailureTests(unittest.TestCase):
    def invoke(self, name, fail):
        with tempfile.TemporaryDirectory(prefix="gos-spy-") as temp:
            root = Path(temp).resolve()
            app, tools = root / "app", root / "bin"
            app.mkdir()
            tools.mkdir()
            for source in [*ROOT.glob("*.ps1"), ROOT / "debloat.sh"]:
                shutil.copyfile(source, app / source.name)
            packages = app / "packages.txt"
            packages.write_bytes(b"com.example.synthetic\n")
            spy = tools / "adb"
            spy.write_text(f"#!{sys.executable}\n" + SPY)
            spy.chmod(0o700)
            assert DIRNAME is not None
            (tools / "dirname").symlink_to(DIRNAME)
            env = {"PATH": str(tools), "HOME": str(root), "TMPDIR": str(root),
                   "XDG_CACHE_HOME": str(root / "cache"), "XDG_CONFIG_HOME": str(root / "config"),
                   "ADB_SPY_ROOT": str(root), "ADB_SPY_SCRIPT": str(app / name),
                   "ADB_SPY_EXPECTED": json.dumps(EXPECTED), "ADB_SPY_FAIL_GOS": str(int(fail)),
                   "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "POWERSHELL_TELEMETRY_OPTOUT": "1"}
            if name.endswith(".ps1"):
                self.assertTrue(PWSH)
                launch = ("$env:PATH = Join-Path $env:ADB_SPY_ROOT 'bin'; "
                          "if ((Get-Command adb -CommandType Application -ErrorAction Stop).Source "
                          "-ne (Join-Path $env:PATH 'adb')) { exit 97 }; & $env:ADB_SPY_SCRIPT")
                argv = [PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", launch]
            else:
                self.assertTrue(BASH)
                argv = [BASH, "-c", '[[ "$(command -v adb)" == "$1" ]] || exit 97; exec "$2" "$3"',
                        "spy-check", str(spy), BASH, str(app / name)]
            result = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=20)
            self.assertNotEqual(result.returncode, 97, "ADB must resolve only to the owned executable spy")
            log = root / "adb.jsonl"
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            receipts = os.environ.get("GOS_TEST_RECEIPTS")
            if receipts:
                out = Path(receipts) / self._testMethodName / (name + "-" + str(fail))
                out.mkdir(parents=True, exist_ok=False)
                (out / "stdout.bin").write_bytes(result.stdout)
                (out / "stderr.bin").write_bytes(result.stderr)
                (out / "adb.jsonl").write_bytes(log.read_bytes())
                (out / "receipt.json").write_text(json.dumps({"argv": argv, "cwd": str(root),
                    "environment": env, "exit": result.returncode, "timeout_seconds": 20,
                    "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in app.iterdir() if p.suffix in (".sh", ".ps1")}}, indent=2) + "\n")
            self.assertEqual(calls, EXPECTED)
            self.assertEqual((app / name).read_bytes(), (ROOT / name).read_bytes())
            self.assertEqual(packages.read_bytes(), b"com.example.synthetic\n")
            return result

    def exercise(self, name):
        result = self.invoke(name, False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"[DONE]", result.stdout)
        result = self.invoke(name, True)
        self.assertNotEqual(result.returncode, 0, "a failed GOS restriction must not be reported as completed")
        self.assertIn(b"[ERROR]", result.stdout + result.stderr)
        self.assertNotIn(b"[DONE]", result.stdout)
        self.assertNotIn(b"[OK]", result.stdout.split(b"Restricting Game Optimizing Service")[-1])

    def test_bash_gos_failure_and_success(self):
        self.exercise("debloat.sh")

    @unittest.skipUnless(PWSH, "native PowerShell unavailable; set POWERSHELL_EXECUTABLE")
    def test_powershell_gos_failure_and_success(self):
        self.exercise("debloat.ps1")


if __name__ == "__main__":
    unittest.main()
