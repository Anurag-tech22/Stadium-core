import subprocess
import os
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    scripts = ["run_scaffold.py", "run_lint.py", "run_security_scan.py", "run_perf.py", "run_a11y.py"]
    
    python_exe = sys.executable
    
    for script in scripts:
        script_path = os.path.join(project_dir, script)
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}")
            continue
            
        print("\n==================================================")
        print(f"Executing: {script}")
        print("==================================================")

        
        # We run using the current python executable (the virtual environment's if run inside it, or system python)
        # Note: the sub-scripts will automatically locate/use the virtualenv `.venv` once launched!
        res = subprocess.run([python_exe, script_path], cwd=project_dir)
        print(f"Finished {script} with exit code: {res.returncode}")

if __name__ == "__main__":
    main()
