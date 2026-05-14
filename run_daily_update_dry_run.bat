@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================
echo  Dry run only: no iFind API call, no quota usage
echo ============================================

where py >nul 2>nul
if %errorlevel%==0 (
    set PY=py -3
) else (
    set PY=python
)

%PY% scripts\ifind_low_quota_daily_update.py --mode dry-run --low-quota --build-signals
pause
