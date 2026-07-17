import os
import subprocess
import sys
import venv

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, ".venv")
    requirements_file = os.path.join(project_dir, "requirements-dev.txt")
    results_file = os.path.join(project_dir, "test_results.txt")

    print(f"Project directory: {project_dir}")
    print(f"Virtual environment directory: {venv_dir}")

    # 1. Create virtual environment if it doesn't exist
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

    # Determine paths to binaries
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        pytest_path = os.path.join(venv_dir, "Scripts", "pytest.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        pytest_path = os.path.join(venv_dir, "bin", "pytest")


    # 2. Install requirements
    print("Installing requirements.txt...")
    install_cmd = [pip_path, "install", "-r", requirements_file]
    print(f"Running command: {' '.join(install_cmd)}")
    
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
        with open(results_file, "w", encoding="utf-8") as f:
            f.write(f"Failed to install requirements.\n\nExit code: {install_res.returncode}\n\nOutput:\n{install_res.stdout}")
        return

    # 3. Run pytest
    pytest_cmd = [pytest_path, "-v"]
    print(f"Running command: {' '.join(pytest_cmd)}")


    
    # We set PYTHONPATH to include the project directory so pytest can find 'app'
    env = os.environ.copy()
    env["PYTHONPATH"] = project_dir

    pytest_res = subprocess.run(
        pytest_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    print(pytest_res.stdout)
    
    # Save the output to test_results.txt
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(pytest_res.stdout)
        
    print(f"Saved complete test results to {results_file}")

if __name__ == "__main__":
    main()
