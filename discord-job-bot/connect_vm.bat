@echo off
echo ==========================================================
echo Connecting to your GCP Free-Tier VM (instance-20260917-061701)...
echo ==========================================================
"%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" compute ssh instance-20260917-061701 --zone=us-central1-a --project=seraphic-rune-366616
pause
