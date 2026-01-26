# GCP Console Setup Checklist

Use this checklist to track your progress through the GCP Console setup.

## ✅ Pre-Deployment Checklist

### Project Setup
- [ ] Created new GCP project (or selected existing)
- [ ] Project ID noted: `_________________`
- [ ] Enabled Compute Engine API
- [ ] Enabled Cloud Build API
- [ ] Enabled Cloud Storage API (if needed)

### Service Account Setup
- [ ] Created service account: `github-actions-deploy`
- [ ] Granted role: Compute Instance Admin
- [ ] Granted role: Service Account User
- [ ] Created JSON key and downloaded
- [ ] JSON key saved securely (will be added to GitHub Secrets)

### VM Instance Setup
- [ ] Created VM instance: `streamlit-app`
- [ ] Region selected: `_________________`
- [ ] Zone selected: `_________________`
- [ ] Machine type: `_________________`
- [ ] Boot disk: Ubuntu 22.04 LTS, 20GB+
- [ ] HTTP traffic enabled
- [ ] HTTPS traffic enabled
- [ ] Network tag added: `streamlit-app`
- [ ] External IP noted: `_________________`

### Firewall Setup
- [ ] Created firewall rule: `allow-streamlit`
- [ ] Port 8501 allowed
- [ ] Target tag: `streamlit-app`

### Initial VM Configuration
- [ ] SSH'd into VM
- [ ] Installed Python 3, pip, git
- [ ] Installed Nginx (optional)
- [ ] Installed Supervisor
- [ ] Cloned repository to `/opt/streamlit-app`
- [ ] Created Python virtual environment
- [ ] Installed requirements.txt
- [ ] Uploaded Google Drive credentials JSON
- [ ] Created systemd service file
- [ ] Enabled and started streamlit service
- [ ] Configured Nginx (if using)

### GitHub Setup
- [ ] Added secret: `GCP_PROJECT_ID`
- [ ] Added secret: `GCP_SA_KEY` (full JSON content)
- [ ] Added secret: `GCP_VM_ZONE`
- [ ] Added secret: `GCP_VM_NAME`
- [ ] Added secret: `GCP_VM_USER`
- [ ] Created `.github/workflows/deploy.yml` file
- [ ] Pushed code to GitHub

### Verification
- [ ] App accessible at `http://EXTERNAL_IP:8501`
- [ ] Tested file upload functionality
- [ ] Tested date range configuration
- [ ] Tested dashboard display
- [ ] Made test commit and verified CI/CD works
- [ ] Checked GitHub Actions workflow runs successfully

## 📝 Important Information to Save

**GCP Project ID**: `_________________`

**VM Details**:
- Name: `streamlit-app`
- Zone: `_________________`
- External IP: `_________________`
- Username: `_________________`

**Service Account Email**: `_________________@_________________.iam.gserviceaccount.com`

**GitHub Repository**: `https://github.com/_________________/_________________`

## 🔒 Security Notes

- [ ] Service account JSON key stored securely
- [ ] Never committed credentials to Git
- [ ] Firewall rules reviewed
- [ ] VM access restricted (if needed)
- [ ] Regular backups configured (optional)

## 🚀 Post-Deployment

- [ ] Set up monitoring alerts
- [ ] Configure budget alerts
- [ ] Set up log aggregation (optional)
- [ ] Configure custom domain (optional)
- [ ] Set up SSL certificate (optional)
