import subprocess

print("Running ruff format...")
res = subprocess.run([r".venv\Scripts\ruff.exe", "format", "app/", "tests/"], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
print(f"Exit code: {res.returncode}")

print("\nRunning ruff format check...")
res2 = subprocess.run([r".venv\Scripts\ruff.exe", "format", "--check", "app/", "tests/"], capture_output=True, text=True)
print("STDOUT:")
print(res2.stdout)
print("Exit code:")
print(res2.returncode)
