# Quick Start: Deploy to GCP in 15 Minutes

This is a condensed version of the full deployment guide. Follow these steps for a quick setup.

## Prerequisites Checklist
- [ ] GCP account with billing enabled
- [ ] GitHub repository with your code
- [ ] Basic terminal/SSH access

---

## Step 1: GCP Console (5 minutes)

### Create Project & Enable APIs
1. Go to [GCP Console](https://console.cloud.google.com/)
2. Create new project: `streamlit-analysis-app`
3. Enable APIs:
   - Compute Engine API
   - Cloud Build API

### Create Service Account
1. **IAM & Admin** → **Service Accounts** → **Create Service Account**
2. Name: `github-actions-deploy`
3. Grant roles:
   - **Compute Instance Admin**
   - **Service Account User**
4. Create JSON key → **Download and save it**

### Create VM
1. **Compute Engine** → **VM instances** → **Create**
2. Settings:
   - Name: `streamlit-app`
   - Region: `us-central1` (or closest)
   - Machine: `e2-medium` (2 vCPU, 4GB RAM)
   - Boot disk: Ubuntu 22.04 LTS, 20GB
   - ✅ Allow HTTP traffic
   - ✅ Allow HTTPS traffic
   - Network tags: `streamlit-app`
3. Click **Create**
4. **Note the External IP**: `_________________`

### Create Firewall Rule
1. **VPC Network** → **Firewall** → **Create**
2. Name: `allow-streamlit`
3. Targets: `streamlit-app` (tag)
4. Ports: `8501`
5. Click **Create**

---

## Step 2: Initial VM Setup (5 minutes)

### SSH into VM
1. Click **SSH** button next to your VM instance

### Run Setup Commands
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3 python3-pip python3-venv git nginx supervisor

# Create app directory
sudo mkdir -p /opt/streamlit-app/app
sudo chown $USER:$USER /opt/streamlit-app
cd /opt/streamlit-app

# Clone your repo (replace with your GitHub URL)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Setup Python environment
cd app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Upload credentials (use SSH file upload or SCP)
# Place your todc-marketing-*.json file in /opt/streamlit-app/app/

# Create systemd service
sudo nano /etc/systemd/system/streamlit.service
```

### Systemd Service Content
```ini
[Unit]
Description=Streamlit App
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/streamlit-app/app
Environment="PATH=/opt/streamlit-app/app/venv/bin"
ExecStart=/opt/streamlit-app/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username (run `whoami`).

### Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

---

## Step 3: GitHub CI/CD Setup (5 minutes)

### Add GitHub Secrets
1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_SA_KEY` | Full contents of downloaded JSON key file |
| `GCP_VM_ZONE` | Your VM zone (e.g., `us-central1-a`) |
| `GCP_VM_NAME` | `streamlit-app` |
| `GCP_VM_USER` | Your VM username |

### Verify Workflow File
- Check that `.github/workflows/deploy.yml` exists in your repo
- If not, copy it from the repository

### Test Deployment
```bash
# Make a small change
echo "# Test" >> README.md
git add .
git commit -m "Test CI/CD"
git push
```

1. Go to GitHub → **Actions** tab
2. Watch the workflow run
3. Wait for completion
4. Check your app at `http://EXTERNAL_IP:8501`

---

## ✅ Verification

- [ ] App loads at `http://EXTERNAL_IP:8501`
- [ ] Can upload files
- [ ] Dashboard displays correctly
- [ ] GitHub Actions workflow completes successfully
- [ ] Changes deploy automatically on push

---

## 🆘 Troubleshooting

**App not accessible?**
- Check firewall allows port 8501
- Verify service is running: `sudo systemctl status streamlit`
- Check logs: `sudo journalctl -u streamlit -f`

**Deployment fails?**
- Verify all GitHub secrets are correct
- Check VM has proper permissions
- Review GitHub Actions logs

**Need help?**
- Check full guide: `DEPLOYMENT_GUIDE.md`
- Review checklist: `GCP_SETUP_CHECKLIST.md`

---

## 🎉 You're Done!

Your app is now live and will automatically deploy on every push to main/master branch.

**Next Steps:**
- Set up custom domain (optional)
- Configure SSL/HTTPS
- Set up monitoring
- Configure backups
