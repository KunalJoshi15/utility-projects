@echo off
powershell.exe -ExecutionPolicy Bypass -File "%~dp0deploy_to_gcp.ps1" %*
pause
