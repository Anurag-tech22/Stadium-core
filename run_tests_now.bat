@echo off
cd /d c:\Users\jagta\phoenix\phoenix-stadium
.venv\Scripts\python.exe -m pytest tests\ -v --tb=short --no-header 2>&1 > test_results.txt
echo Exit code: %ERRORLEVEL%
type test_results.txt
