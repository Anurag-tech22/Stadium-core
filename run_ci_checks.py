import subprocess
import sys

def run_step(name, cmd_args):
    print(f"\n==================== RUNNING: {name} ====================")
    res = subprocess.run(cmd_args, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)
    print(f"Exit code: {res.returncode}")
    return res.returncode == 0

all_ok = True
all_ok &= run_step("Ruff Lint", [r".venv\Scripts\ruff.exe", "check", "app/", "tests/"])
all_ok &= run_step("Ruff Format Check", [r".venv\Scripts\ruff.exe", "format", "--check", "app/", "tests/"])
all_ok &= run_step("Mypy Type-Check", [r".venv\Scripts\mypy.exe", "app/", "--ignore-missing-imports"])
all_ok &= run_step("Bandit Security Scan", [r".venv\Scripts\bandit.exe", "-r", "app/", "-ll", "-q"])
all_ok &= run_step("Pip Audit", [r".venv\Scripts\pip-audit.exe", "--requirement", "requirements.txt", "--ignore-vuln", "PYSEC-2024-2"])
all_ok &= run_step("Pytest with Coverage (fail under 90)", [
    r".venv\Scripts\pytest.exe", "tests/", "-v",
    "--cov=app", "--cov-report=term-missing", "--cov-fail-under=90"
])

if all_ok:
    print("\n🎉 ALL CI CHECKS PASS LOCALLY!")
    sys.exit(0)
else:
    print("\n❌ SOME CI CHECKS FAILED LOCALLY!")
    sys.exit(1)
