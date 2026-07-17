@echo off
echo ==================================================
echo CLEANING PROJECT CLUTTER FOR GITHUB SUBMISSION
echo ==================================================
echo.

echo Removing cache directories...
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .ruff_cache rmdir /s /q .ruff_cache
if exist .mypy_cache rmdir /s /q .mypy_cache

echo Removing virtual environment (if any)...
if exist .venv rmdir /s /q .venv

echo Removing auxiliary scratch/log files...
if exist test_results.txt del /f /q test_results.txt
if exist verify_logic.py del /f /q verify_logic.py
if exist run_all.py del /f /q run_all.py
if exist run_lint.py del /f /q run_lint.py
if exist run_perf.py del /f /q run_perf.py
if exist run_a11y.py del /f /q run_a11y.py
if exist run_scaffold.py del /f /q run_scaffold.py
if exist run_security_scan.py del /f /q run_security_scan.py
if exist run_ruff_fix.py del /f /q run_ruff_fix.py
if exist run_failing_tests.py del /f /q run_failing_tests.py
if exist simple_push.bat del /f /q simple_push.bat
if exist run_tests_now.bat del /f /q run_tests_now.bat
if exist push_clean.bat del /f /q push_clean.bat
if exist push_fixes.bat del /f /q push_fixes.bat

echo Removing local Git integration...
if exist .git rmdir /s /q .git

echo.
echo PROJECT IS NOW CLEAN! All non-essential files and Git logs are removed.
echo.
pause
