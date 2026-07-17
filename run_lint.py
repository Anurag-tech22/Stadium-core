import os
import subprocess
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, ".venv")
    requirements_file = os.path.join(project_dir, "requirements-dev.txt")
    
    docs_dir = os.path.join(project_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    report_file = os.path.join(docs_dir, "lint-report.txt")

    print(f"Project directory: {project_dir}")
    print(f"Virtual environment directory: {venv_dir}")

    # Determine paths to binaries
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        ruff_path = os.path.join(venv_dir, "Scripts", "ruff.exe")
        mypy_path = os.path.join(venv_dir, "Scripts", "mypy.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        ruff_path = os.path.join(venv_dir, "bin", "ruff")
        mypy_path = os.path.join(venv_dir, "bin", "mypy")

    # 1. Update/install dependencies (ensures ruff and mypy are installed)
    print("Installing/Updating requirements-dev.txt...")
    install_cmd = [pip_path, "install", "-r", requirements_file]
    install_res = subprocess.run(
        install_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(install_res.stdout)
    if install_res.returncode != 0:
        print("Failed to install requirements.")
        return

    # 2. Run Ruff
    print("Running ruff check . ...")
    ruff_cmd = [ruff_path, "check", "."]
    ruff_res = subprocess.run(
        ruff_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("--- Ruff Output ---")
    print(ruff_res.stdout)
    print("-------------------")

    # 3. Run Mypy
    print("Running mypy app/ ...")
    mypy_cmd = [mypy_path, "app/"]
    # We set PYTHONPATH to include the project directory
    env = os.environ.copy()
    env["PYTHONPATH"] = project_dir
    mypy_res = subprocess.run(
        mypy_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    print("--- Mypy Output ---")
    print(mypy_res.stdout)
    print("-------------------")

    # 4. Save report
    report_content = (
        "=== RUFF CHECK OUTPUT ===\n"
        f"{ruff_res.stdout}\n"
        "=========================\n\n"
        "=== MYPY CHECK OUTPUT ===\n"
        f"{mypy_res.stdout}\n"
        "=========================\n"
    )
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Saved linting report to {report_file}")

if __name__ == "__main__":
    main()
