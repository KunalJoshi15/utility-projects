@echo off
cd /d "%~dp0"
echo ===================================================
echo 🚀 Deploying Study Tracker to GCP VM
echo Instance: instance-20260917-061701 (us-central1-a)
echo Project:  seraphic-rune-366616
echo ===================================================

echo.
echo [1/2] Syncing study-tracker files to GCP VM...
gcloud.cmd compute scp --recurse bot config database services tests main.py requirements.txt instance-20260917-061701:/opt/study-tracker/ --zone=us-central1-a --project=seraphic-rune-366616

if %ERRORLEVEL% NEQ 0 (
    echo ❌ File sync failed. Check your gcloud authentication.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Restarting study-tracker.service on GCP VM...
gcloud.cmd compute ssh instance-20260917-061701 --zone=us-central1-a --project=seraphic-rune-366616 --command="sudo systemctl restart study-tracker.service; sudo systemctl status study-tracker.service --no-pager"

echo.
echo ===================================================
echo ✅ Deployment Complete! Study Tracker is live on GCP.
echo ===================================================
pause
