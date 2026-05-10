@echo off
cd /d %~dp0\..
python local_tools\build_deploy_data.py
pause
