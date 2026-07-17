import subprocess
import sys

# Kill any locked processes using pytest or ruff in the background
subprocess.run(["taskkill", "/F", "/IM", "pytest.exe"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "ruff.exe"], capture_output=True)

print("Installing requirements-dev.txt dependencies locally...")
# Try to upgrade only Ruff in the virtual environment (bypassing the pytest.exe lock)
print("Upgrading Ruff to version 0.15.22 locally...")
res = subprocess.run([r".venv\Scripts\python.exe", "-m", "pip", "install", "ruff==0.15.22"], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
print(f"Exit code: {res.returncode}")

if res.returncode == 0:
    print("\nRunning Ruff format on all files with updated version...")
    res2 = subprocess.run([r".venv\Scripts\ruff.exe", "format", "app/", "tests/"], capture_output=True, text=True)
    print("STDOUT:")
    print(res2.stdout)
    print(f"Exit code: {res2.returncode}")
else:
    print("Failed to upgrade Ruff.")
