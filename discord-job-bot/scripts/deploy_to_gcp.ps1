# ==============================================================================
# 1-Click GCP Free-Tier Deployment Script for Discord Job Bot
# ==============================================================================

param (
    [string]$ProjectId = "",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "discord-job-bot-free-vm"
)

$gcloud = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloud)) {
    $gcloud = "gcloud"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 Google Cloud Platform (GCP) 100% Free-Tier Deployment" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Project Selection
if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Host "`nAvailable GCP Projects:" -ForegroundColor Yellow
    & $gcloud projects list
    $ProjectId = Read-Host "`nEnter the Project ID you want to use (e.g. seraphic-rune-366616)"
}

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Host "❌ Project ID cannot be empty." -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/5] Setting active project to: $ProjectId..." -ForegroundColor Cyan
& $gcloud config set project $ProjectId

Write-Host "`n[2/5] Enabling Compute Engine API (if not already enabled)..." -ForegroundColor Cyan
& $gcloud services enable compute.googleapis.com

Write-Host "`n[3/5] Creating 100% Free-Tier VM ($InstanceName in $Zone)..." -ForegroundColor Cyan
Write-Host "  - Machine Type: e2-micro (Always Free)" -ForegroundColor DarkGray
Write-Host "  - Region: us-central1 (Always Free eligible)" -ForegroundColor DarkGray
Write-Host "  - Boot Disk: 25GB Standard Persistent Disk" -ForegroundColor DarkGray

# Check if instance already exists
$existingVm = & $gcloud compute instances list --filter="name=($InstanceName)" --format="value(name)"
if ($existingVm -eq $InstanceName) {
    Write-Host "  ⚠️ Instance '$InstanceName' already exists. Reusing existing VM." -ForegroundColor Yellow
} else {
    & $gcloud compute instances create $InstanceName `
        --zone=$Zone `
        --machine-type=e2-micro `
        --image-family=ubuntu-2204-lts `
        --image-project=ubuntu-os-cloud `
        --boot-disk-size=25GB `
        --boot-disk-type=pd-standard `
        --tags=discord-bot
}

Write-Host "`n[4/5] Preparing and copying project files to the VM..." -ForegroundColor Cyan
# Wait a few seconds for SSH to initialize if newly created
Start-Sleep -Seconds 10

# Create remote directory
& $gcloud compute ssh $InstanceName --zone=$Zone --command="sudo mkdir -p /opt/discord-job-bot && sudo chown -R `$USER:`$USER /opt/discord-job-bot"

# Copy project files using gcloud scp (excluding venv and local data)
$projectRoot = Resolve-Path "$PSScriptRoot\.."
& $gcloud compute scp --recurse `
    "$projectRoot\bot" `
    "$projectRoot\config" `
    "$projectRoot\database" `
    "$projectRoot\services" `
    "$projectRoot\scripts" `
    "$projectRoot\main.py" `
    "$projectRoot\Dockerfile" `
    "$projectRoot\docker-compose.yml" `
    "$projectRoot\requirements.txt" `
    "$projectRoot\.env" `
    "${InstanceName}:/opt/discord-job-bot/" `
    --zone=$Zone

Write-Host "`n[5/5] Running Bootstrap Script (Configuring 4GB Swap Space & Docker Systemd)..." -ForegroundColor Cyan
& $gcloud compute ssh $InstanceName --zone=$Zone --command="cd /opt/discord-job-bot && chmod +x scripts/setup_gcp_vm.sh && sudo ./scripts/setup_gcp_vm.sh && sudo systemctl restart discord-job-bot"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT COMPLETE! Bot is now running 24/7 on GCP!" -ForegroundColor Green
Write-Host "Monthly Hosting Cost: $0.00 (100% Free Tier)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "`nHelpful management commands:" -ForegroundColor Yellow
Write-Host "  - View live logs:    & `"$gcloud`" compute ssh $InstanceName --zone=$Zone --command=`"sudo journalctl -u discord-job-bot -f`""
Write-Host "  - Restart bot:       & `"$gcloud`" compute ssh $InstanceName --zone=$Zone --command=`"sudo systemctl restart discord-job-bot`""
Write-Host "  - SSH into VM:       & `"$gcloud`" compute ssh $InstanceName --zone=$Zone"
