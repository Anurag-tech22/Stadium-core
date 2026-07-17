import os
import subprocess
import time
import sys
import socket


def wait_for_server(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    return False

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, ".venv")
    
    docs_dir = os.path.join(project_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    report_file = os.path.join(docs_dir, "accessibility-report.txt")

    print(f"Project directory: {project_dir}")
    print(f"Virtual environment directory: {venv_dir}")

    # Determine paths to binaries
    if sys.platform == "win32":
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_dir, "bin", "python")

    # 1. Start uvicorn server in background
    port = 8000
    server_cmd = [python_path, "-m", "uvicorn", "app.main:app", "--port", str(port)]
    print(f"Starting server in background: {' '.join(server_cmd)}")
    
    server_process = subprocess.Popen(
        server_cmd,
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    try:
        # Wait for port 8000 to become active
        if not wait_for_server(port, timeout=15):
            print("Timed out waiting for local dev server to start.")
            # Print whatever output the server produced
            stdout, _ = server_process.communicate(timeout=1)
            print(stdout)
            return

        print("Dev server started successfully on port 8000.")

        # 2. Run axe-core CLI via npx against both endpoints
        print("Running axe check for http://localhost:8000/ ...")
        # -y automatically answers yes to install questions from npx
        axe_cmd_home = ["npx", "-y", "@axe-core/cli", "http://localhost:8000/"]
        print(f"Running command: {' '.join(axe_cmd_home)}")
        axe_res_home = subprocess.run(
            axe_cmd_home,
            shell=True if sys.platform == "win32" else False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print("--- Home Page axe Output ---")
        print(axe_res_home.stdout)
        print("----------------------------")

        print("Running axe check for http://localhost:8000/ops ...")
        axe_cmd_ops = ["npx", "-y", "@axe-core/cli", "http://localhost:8000/ops"]
        print(f"Running command: {' '.join(axe_cmd_ops)}")
        axe_res_ops = subprocess.run(
            axe_cmd_ops,
            shell=True if sys.platform == "win32" else False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print("--- Ops Dashboard axe Output ---")
        print(axe_res_ops.stdout)
        print("--------------------------------")

        # 3. Save report
        report_content = (
            "=== ACCESSIBILITY REPORT - HOME PAGE (/) ===\n"
            f"{axe_res_home.stdout}\n"
            "===========================================\n\n"
            "=== ACCESSIBILITY REPORT - OPS DASHBOARD (/ops) ===\n"
            f"{axe_res_ops.stdout}\n"
            "===================================================\n"
        )
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"Saved accessibility report to {report_file}")

    finally:
        print("Terminating dev server background process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("Dev server stopped.")
        except subprocess.TimeoutExpired:
            print("Force killing dev server...")
            server_process.kill()
            server_process.wait()
            print("Dev server force killed.")

if __name__ == "__main__":
    main()

