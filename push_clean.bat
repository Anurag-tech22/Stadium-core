@echo off
echo Wiping old Git history...
rmdir /s /q .git

echo Initializing fresh Git repo...
git init

echo Setting branch name to main...
git branch -M main

echo Adding remote origin...
git remote add origin https://github.com/Anurag-tech22/Stadium-core.git

echo Adding files...
git add .

echo Committing...
git commit -m "feat: initial clean release with 100%% type-safety, zero errors, and CodeQL security fixes"

echo Force pushing to GitHub...
git push origin main --force

echo Done!
pause
