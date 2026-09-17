@echo off
cd /d "%~dp0"
echo ===================================================
echo 🚀 Deploying Local Changes to GCP Always Free VM
echo Instance: instance-20260917-061701 (us-central1-a)
echo Project:  seraphic-rune-366616
echo ===================================================

echo.
echo [1/2] Syncing updated source files to GCP VM...
gcloud.cmd compute scp --recurse bot services database config tests main.py docker-compose.yml instance-20260917-061701:/opt/discord-job-bot/ --zone=us-central1-a --project=seraphic-rune-366616

if %ERRORLEVEL% NEQ 0 (
    echo ❌ File sync failed. Check your gcloud authentication.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Restarting discord-job-bot.service on GCP VM...
gcloud.cmd compute ssh instance-20260917-061701 --zone=us-central1-a --project=seraphic-rune-366616 --command="sudo systemctl restart discord-job-bot.service; sudo systemctl status discord-job-bot.service --no-pager"

echo.
echo ===================================================
echo ✅ Deployment Complete! Bot is running live on GCP.
echo ===================================================
pause
