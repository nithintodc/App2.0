# Deployment Guide: Streamlit App on GCP Compute Engine

This guide will help you deploy the Streamlit application to Google Cloud Platform (GCP) Compute Engine with GitHub CI/CD for continuous deployment.

## Prerequisites

- Google Cloud Platform account
- GitHub repository with your code
- Basic knowledge of GCP Console and GitHub

---

## Part 1: GCP Console Setup

### Step 1: Create a New Project (if needed)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter project name: `streamlit-analysis-app` (or your preferred name)
5. Click **"Create"**
6. Wait for project creation, then select the new project

### Step 2: Enable Required APIs

1. Go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Compute Engine API**
   - **Cloud Build API** (for CI/CD)
   - **Cloud Storage API** (if needed for file storage)

### Step 3: Create Service Account for GitHub Actions

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **"Create Service Account"**
3. Name: `github-actions-deploy`
4. Description: `Service account for GitHub Actions CI/CD`
5. Click **"Create and Continue"**
6. Grant roles:
   - **Compute Instance Admin** (to manage VMs)
   - **Service Account User**
   - **Storage Admin** (if using Cloud Storage)
7. Click **"Continue"** → **"Done"**
8. Click on the created service account
9. Go to **"Keys"** tab
10. Click **"Add Key"** → **"Create new key"**
11. Select **JSON** format
12. Click **"Create"** - This downloads a JSON key file
13. **IMPORTANT**: Save this file securely - you'll need it for GitHub Secrets

### Step 4: Create Compute Engine VM Instance

1. Go to **Compute Engine** → **VM instances**
2. Click **"Create Instance"**

#### Basic Settings:
- **Name**: `streamlit-app`
- **Region**: Choose closest to your users (e.g., `us-central1`)
- **Zone**: Any zone in the selected region

#### Machine Configuration:
- **Machine family**: General-purpose
- **Series**: N1 (or E2 for cost savings)
- **Machine type**: 
  - **e2-medium** (2 vCPU, 4 GB RAM) - Recommended for small apps
  - **e2-standard-2** (2 vCPU, 8 GB RAM) - For larger datasets
  - **n1-standard-1** (1 vCPU, 3.75 GB RAM) - Minimum viable

#### Boot Disk:
- **Operating System**: Ubuntu
- **Version**: Ubuntu 22.04 LTS (or latest LTS)
- **Boot disk type**: Standard persistent disk
- **Size**: 20 GB (minimum) - Increase if you expect large file uploads
- Click **"Select"**

#### Firewall:
- ✅ **Allow HTTP traffic**
- ✅ **Allow HTTPS traffic**

#### Advanced Options (Optional but Recommended):
1. Click **"Networking"** tab
2. Under **"Network tags"**, add: `streamlit-app`
3. Click **"Create"**

### Step 5: Configure Firewall Rules

1. Go to **VPC Network** → **Firewall**
2. Click **"Create Firewall Rule"**
3. **Name**: `allow-streamlit`
4. **Direction**: Ingress
5. **Targets**: Specified target tags
6. **Target tags**: `streamlit-app`
7. **Source IP ranges**: `0.0.0.0/0` (or restrict to specific IPs)
8. **Protocols and ports**: 
   - ✅ **TCP**
   - **Ports**: `8501` (Streamlit default port)
9. Click **"Create"**

### Step 6: Get VM External IP

1. Go back to **Compute Engine** → **VM instances**
2. Find your `streamlit-app` instance
3. Note the **External IP** address (e.g., `34.123.45.67`)
4. You'll use this to access your app

---

## Part 2: Initial VM Setup (One-time)

### Step 7: SSH into VM

1. In **VM instances**, click **"SSH"** next to your instance
2. This opens a browser-based terminal

### Step 8: Install Required Software

Run these commands in the SSH terminal:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.10+ and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install Git
sudo apt-get install -y git

# Install Nginx (for reverse proxy - optional but recommended)
sudo apt-get install -y nginx

# Install Supervisor (for process management)
sudo apt-get install -y supervisor

# Verify installations
python3 --version
pip3 --version
git --version
```

### Step 9: Create Application Directory

```bash
# Create app directory
sudo mkdir -p /opt/streamlit-app
sudo chown $USER:$USER /opt/streamlit-app
cd /opt/streamlit-app

# Clone your repository (replace with your repo URL)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git .

# Or if using SSH:
# git clone git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git .
```

### Step 10: Set Up Python Environment

```bash
cd /opt/streamlit-app/app

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install gunicorn for production (optional)
pip install gunicorn
```

### Step 11: Upload Google Drive Credentials

```bash
# Create credentials directory
mkdir -p /opt/streamlit-app/app

# Upload your Google Drive service account JSON file
# Use the upload option in the SSH terminal or SCP from local machine:
# scp -i ~/.ssh/gcp_key path/to/todc-marketing-ad02212d4f16.json USER@EXTERNAL_IP:/opt/streamlit-app/app/
```

### Step 12: Create Systemd Service (for auto-start)

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Add this content:

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

Replace `YOUR_USERNAME` with your actual username (run `whoami` to find it).

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

### Step 13: Set Up Nginx Reverse Proxy (Optional but Recommended)

```bash
sudo nano /etc/nginx/sites-available/streamlit
```

Add this content:

```nginx
server {
    listen 80;
    server_name YOUR_EXTERNAL_IP_OR_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Part 3: GitHub CI/CD Setup

### Step 14: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add these secrets:

#### Secret 1: `GCP_PROJECT_ID`
- **Name**: `GCP_PROJECT_ID`
- **Value**: Your GCP project ID (found in GCP Console)

#### Secret 2: `GCP_SA_KEY`
- **Name**: `GCP_SA_KEY`
- **Value**: The entire contents of the JSON key file you downloaded in Step 3
- **Important**: Copy the entire JSON content, including `{` and `}`

#### Secret 3: `GCP_VM_ZONE`
- **Name**: `GCP_VM_ZONE`
- **Value**: Your VM zone (e.g., `us-central1-a`)

#### Secret 4: `GCP_VM_NAME`
- **Name**: `GCP_VM_NAME`
- **Value**: `streamlit-app` (or your VM name)

#### Secret 5: `GCP_VM_USER`
- **Name**: `GCP_VM_USER`
- **Value**: Your VM username (usually the same as your GCP account username)

### Step 15: Create GitHub Actions Workflow

The workflow file is already created at `.github/workflows/deploy.yml`. Make sure it exists and is configured correctly.

---

## Part 4: Verify Deployment

### Step 16: Test the Application

1. Open your browser
2. Navigate to: `http://YOUR_EXTERNAL_IP:8501`
   - Or if using Nginx: `http://YOUR_EXTERNAL_IP`
3. You should see the Streamlit upload screen

### Step 17: Test CI/CD

1. Make a small change to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push
   ```
3. Go to GitHub → **Actions** tab
4. You should see a workflow running
5. Wait for it to complete
6. Refresh your app - changes should be live!

---

## Part 5: Monitoring and Maintenance

### View Logs

```bash
# Streamlit logs
sudo journalctl -u streamlit -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Service

```bash
sudo systemctl restart streamlit
```

### Update Application Manually (if needed)

```bash
cd /opt/streamlit-app
git pull
cd app
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart streamlit
```

---

## Troubleshooting

### App not accessible
- Check firewall rules allow port 8501
- Verify VM has external IP
- Check service status: `sudo systemctl status streamlit`

### Deployment fails
- Verify GitHub secrets are correct
- Check VM has proper permissions
- Review GitHub Actions logs

### Permission errors
- Ensure service account has correct roles
- Check file permissions in `/opt/streamlit-app`

---

## Cost Optimization Tips

1. **Use Preemptible VMs** (60-90% cheaper, but can be terminated)
2. **Set up auto-shutdown** during off-hours
3. **Use smaller machine types** if performance allows
4. **Enable Cloud Monitoring** to track usage
5. **Set budget alerts** in GCP Console

---

## Security Best Practices

1. **Restrict firewall** to specific IP ranges if possible
2. **Use HTTPS** with SSL certificate (Let's Encrypt)
3. **Regular updates**: `sudo apt-get update && sudo apt-get upgrade`
4. **Secure credentials**: Never commit service account keys
5. **Use IAM roles** with least privilege principle

---

## Next Steps

- Set up custom domain (optional)
- Configure SSL certificate for HTTPS
- Set up monitoring and alerts
- Configure automated backups
- Set up log aggregation

---

## Support

For issues:
1. Check GitHub Actions logs
2. Check VM system logs
3. Review GCP Console logs
4. Check Streamlit application logs
