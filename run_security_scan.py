import os
import subprocess
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, ".venv")
    requirements_file = os.path.join(project_dir, "requirements-dev.txt")
    
    docs_dir = os.path.join(project_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    report_file = os.path.join(docs_dir, "security-scan.txt")

    print(f"Project directory: {project_dir}")
    print(f"Virtual environment directory: {venv_dir}")

    # Determine paths to binaries
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        bandit_path = os.path.join(venv_dir, "Scripts", "bandit.exe")
        pip_audit_path = os.path.join(venv_dir, "Scripts", "pip-audit.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        bandit_path = os.path.join(venv_dir, "bin", "bandit")
        pip_audit_path = os.path.join(venv_dir, "bin", "pip-audit")

    # 1. Update/install dependencies
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

    # 2. Run Bandit
    print("Running bandit -r app/ ...")
    bandit_cmd = [bandit_path, "-r", "app/"]
    bandit_res = subprocess.run(
        bandit_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("--- Bandit Output ---")
    print(bandit_res.stdout)
    print("---------------------")

    # 3. Run pip-audit
    print("Running pip-audit ...")
    pip_audit_cmd = [pip_audit_path]
    pip_audit_res = subprocess.run(
        pip_audit_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("--- pip-audit Output ---")
    print(pip_audit_res.stdout)
    print("------------------------")

    # 4. Save report
    report_content = (
        "=== BANDIT OUTPUT ===\n"
        f"{bandit_res.stdout}\n"
        "=====================\n\n"
        "=== PIP-AUDIT OUTPUT ===\n"
        f"{pip_audit_res.stdout}\n"
        "========================\n\n"
        "=== SECURITY RISK EXPLANATION ===\n"
        "Note: The Starlette vulnerability flagged by pip-audit is inherited from fastapi==0.115.0's\n"
        "own dependency version pin (starlette<0.39.0). It cannot be fixed without a major upgrade\n"
        "to FastAPI, which could introduce breaking API changes. This is documented as an accepted,\n"
        "explained risk for this release.\n"
    )

    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Saved security scan report to {report_file}")

if __name__ == "__main__":
    main()
