# 100% Free Tier GCP Deployment Guide: Discord Job & AI Resume Bot

This guide walks you through deploying your bot to **Google Cloud Platform (GCP)** so that it runs **24/7 permanently with $0.00 hosting cost**.

---

## 💰 Understanding the GCP "Always Free" Tier

Google Cloud offers an **Always Free Tier** that never expires as long as you stay within these parameters:

| Resource | GCP Always Free Limit | Bot Configuration | Cost |
|---|---|---|---|
| **Compute Engine** | 1 non-preemptible `e2-micro` VM per month | `e2-micro` (2 vCPUs, 1 GB RAM + 4GB Swap) | **$0.00 / mo** |
| **Eligible Regions** | `us-central1` (Iowa), `us-east1` (S. Carolina), `us-west1` (Oregon) | Any of the 3 US Free regions | **$0.00 / mo** |
| **Persistent Disk** | Up to 30 GB Standard persistent disk | 25 GB Standard persistent disk | **$0.00 / mo** |
| **Network Egress** | 1 GB egress per month to North America / worldwide | Bot sends lightweight Discord payloads & screenshots | **$0.00 / mo** |
| **Google Gemini AI** | Free RPM/TPM allowances in Google AI Studio | Standard free rate tier | **$0.00 / mo** |
| **Database** | Embedded SQLite on persistent disk (no Cloud SQL) | Local `/app/data/bot.db` | **$0.00 / mo** |

> [!TIP]
> **Total Monthly Cost: $0.00**

---

## Part 1: Setting Up Your Discord Bot & Gemini API Key

### 1. Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Create **New Application** > **Bot** > **Reset Token** > Copy your token.
3. Under **Privileged Gateway Intents**, enable:
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
4. Under **OAuth2 > URL Generator**, select `bot` + `applications.commands` and invite the bot to your Discord server.

### 2. Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** > **Create API key**.
3. Copy your `GEMINI_API_KEY`.

---

## Part 2: Creating the $0 GCP Free Tier VM

### 1. Via GCP Web Console:
1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Go to **Compute Engine > VM instances**.
3. Click **Create Instance**:
   - **Name**: `discord-bot-free-vm`
   - **Region**: Select **`us-central1` (Iowa)**, **`us-east1` (S. Carolina)**, or **`us-west1` (Oregon)** *(Required for Free Tier)*.
   - **Machine Configuration**: `e2-micro` (2 vCPU, 1 GB memory).
   - **Boot Disk**: Click **Change** > Select **Ubuntu 22.04 LTS** > Set size to **25 GB** (Standard Persistent Disk).
   - **Firewall**: Default settings.
4. Click **Create**.

### 2. Via `gcloud` CLI (Single Command):
```bash
gcloud compute instances create discord-bot-free-vm \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=25GB \
    --boot-disk-type=pd-standard
```

---

## Part 3: Deploying the Bot & Enabling 4GB Swap Space

### 1. Connect to your VM via SSH
Click **SSH** next to `discord-bot-free-vm` in the GCP Console, or run:
```bash
gcloud compute ssh discord-bot-free-vm --zone=us-central1-a
```

### 2. Clone the repository and run the Free Tier Setup Script
```bash
git clone https://github.com/your-username/discord-job-bot.git /opt/discord-job-bot
cd /opt/discord-job-bot
chmod +x scripts/setup_gcp_vm.sh
./scripts/setup_gcp_vm.sh
```

*(This automatically configures a **4GB swapfile** to ensure Playwright headless browser and AI resume tasks run smoothly without RAM exhaustion).*

### 3. Create your `.env` File
```bash
cd /opt/discord-job-bot
nano .env
```
Paste:
```env
DISCORD_BOT_TOKEN=your_real_discord_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
RAPIDAPI_KEY=
LOG_LEVEL=INFO
```
Save with `Ctrl+O`, `Enter`, `Ctrl+X`.

### 4. Start the 24/7 Daemon Service
```bash
sudo systemctl start discord-job-bot
```

To enable auto-start on server reboots:
```bash
sudo systemctl enable discord-job-bot
```

---

## Part 4: Monitoring, Logs & Verification

### Stream Live Logs
```bash
# View systemd service logs in real time
sudo journalctl -u discord-job-bot -f

# Or view Docker logs
sudo docker logs -f discord_job_bot
```

### Check Swap & Memory Usage
```bash
free -h
```
*(You will see 1GB RAM + 4GB Swap active!)*

---

## Part 5: Discord Commands Summary

| Command | Action |
|---|---|
| `/jobs search <query> [location]` | Search jobs across LinkedIn, Naukri, and career portals |
| `/jobs match` | AI matches openings tailored to your uploaded resume |
| `/jobs view <job_id>` | View full requirements, salary, and company profile |
| `/jobs apply <job_id>` | Headless browser auto-apply with screenshot proof |
| `/resume review` | Gemini AI audit of your resume: flaws, ATS score & rewrites |
| `/resume parse` | Auto-syncs your Discord profile from your resume text |
| `/profile setup` | Configure contact info, links, and preferences |
| `/profile resume` | Drag-and-drop resume PDF upload |
| `/profile cookie` | Encrypted storage for LinkedIn session cookie |
| `/applications list` | Application history and submission status |
