# Deploy This App to a Google Cloud VM

Step-by-step guide to run the Streamlit app on a Google Cloud Platform (GCP) Compute Engine virtual machine and access it from the internet.

**Quick links:** Checklist → **GCP_SETUP_CHECKLIST.md** | Full deployment details → **DEPLOYMENT_GUIDE.md** | This guide = short path to a working VM.

---

## What You’ll Have When Done

- A VM on GCP running Ubuntu
- The app running 24/7 and reachable at `http://<VM-EXTERNAL-IP>:8501`
- Optional: push code from your machine → VM updates automatically (CI/CD)

---

## Part 1: One-Time GCP Setup

### 1.1 Create or Select a GCP Project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Use the project dropdown → **New Project** (or pick an existing one).
3. Note the **Project ID** (e.g. `my-streamlit-project`). You’ll need it later.

### 1.2 Enable Compute Engine

1. In the console, go to **APIs & Services** → **Library**.
2. Search for **Compute Engine API** and open it.
3. Click **Enable**.

### 1.3 Create a VM Instance

1. Go to **Compute Engine** → **VM instances**.
2. Click **Create Instance**.

Use these settings (or adjust as needed):

| Setting        | Value |
|----------------|--------|
| **Name**       | `streamlit-app` (or any name) |
| **Region**     | e.g. `us-central1` |
| **Zone**       | e.g. `us-central1-a` |
| **Machine type** | **e2-medium** (2 vCPU, 4 GB) or **e2-small** (2 vCPU, 2 GB) |
| **Boot disk**  | **Ubuntu 22.04 LTS**, 20 GB |
| **Firewall**   | ✅ Allow HTTP traffic, ✅ Allow HTTPS traffic |

3. Under **Networking** → **Network tags**, add: `streamlit-app`.
4. Click **Create**.

Note the **External IP** of the VM (e.g. `34.123.45.67`).

### 1.4 Open Port 8501 on the Firewall

1. Go to **VPC network** → **Firewall**.
2. Click **Create firewall rule**.
3. Use:
   - **Name**: `allow-streamlit`
   - **Direction**: Ingress
   - **Targets**: Specified target tags → **Target tags**: `streamlit-app`
   - **Source IP ranges**: `0.0.0.0/0` (or your office IP for more security)
   - **Protocols and ports**: **TCP** → **Ports**: `8501`
4. Click **Create**.

---

## Part 2: One-Time VM Setup (SSH)

### 2.1 Connect to the VM

1. In **Compute Engine** → **VM instances**, click **SSH** next to your instance (browser SSH window opens).

### 2.2 Install Dependencies

Run in the SSH terminal:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git
```

Check:

```bash
python3 --version   # 3.10+ preferred
pip3 --version
```

### 2.3 Create App Directory and Clone Your Code

Replace `YOUR_GITHUB_USER` and `YOUR_REPO` with your actual GitHub repo:

```bash
sudo mkdir -p /opt/streamlit-app
sudo chown $USER:$USER /opt/streamlit-app
cd /opt/streamlit-app

# Clone the whole repo (you’ll run the app from the app/ subfolder)
git clone https://github.com/YOUR_GITHUB_USER/YOUR_REPO.git .
```

If your repo is private, use a personal access token or SSH key, or upload the code another way (see “Alternative: Upload Code Without Git” below).

### 2.4 Set Up Python and Install Packages

```bash
cd /opt/streamlit-app/app

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2.5 (Optional) Add Google Drive Credentials

If the app uses Google Drive:

1. On your computer, copy your service account JSON key (e.g. `todc-marketing-ad02212d4f16.json`).
2. In the SSH window, click **Settings (gear)** → **Upload file** and choose that JSON.
3. Move it into the app folder:

```bash
mv ~/todc-marketing-ad02212d4f16.json /opt/streamlit-app/app/
```

Or from your **local** machine (replace `YOUR_KEY_FILE.json` and `EXTERNAL_IP`):

```bash
gcloud compute scp YOUR_KEY_FILE.json EXTERNAL_IP:/opt/streamlit-app/app/ --zone=YOUR_ZONE
```

### 2.6 Create a Service So the App Starts on Boot

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Paste this (replace `YOUR_LINUX_USER` with the output of `whoami`):

```ini
[Unit]
Description=Streamlit App
After=network.target

[Service]
Type=simple
User=YOUR_LINUX_USER
WorkingDirectory=/opt/streamlit-app/app
Environment="PATH=/opt/streamlit-app/app/venv/bin"
ExecStart=/opt/streamlit-app/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save (Ctrl+O, Enter) and exit (Ctrl+X). Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

You should see `active (running)`.

---

## Part 3: Use the App

1. In a browser open: **`http://<VM-EXTERNAL-IP>:8501`**
2. You should see the Streamlit app (e.g. upload / analysis screen).

If it doesn’t load:

- Confirm the firewall rule `allow-streamlit` exists and allows TCP 8501 for tag `streamlit-app`.
- On the VM: `sudo systemctl status streamlit` and `sudo journalctl -u streamlit -n 50`.

---

## Part 4: Optional – Auto-Deploy on Git Push (CI/CD)

So that every push to GitHub updates the app on the VM.

### 4.1 Create a GCP Service Account for Deployment

1. In GCP: **IAM & Admin** → **Service Accounts** → **Create Service Account**.
2. Name: `github-deploy`.
3. Grant roles: **Compute Instance Admin (v1)** and **Service Account User**.
4. Create a **JSON key** and download it. Keep it secret.

### 4.2 Add GitHub Secrets

In your GitHub repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add:

| Secret name     | Value |
|-----------------|--------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_SA_KEY`     | **Entire** contents of the JSON key file |
| `GCP_VM_ZONE`    | VM zone, e.g. `us-central1-a` |
| `GCP_VM_NAME`    | VM name, e.g. `streamlit-app` |
| `GCP_VM_USER`    | Linux username on the VM (from `whoami` on SSH) |

### 4.3 Allow the Service Account to Use the VM

1. In GCP: **Compute Engine** → **VM instances**.
2. Open your VM → **Edit**.
3. Under **Access** (or **Security**), add the service account `github-deploy@YOUR_PROJECT.iam.gserviceaccount.com` with “Compute Instance Admin” or “Editor” if needed for SSH/SCP.

### 4.4 Use the Existing Workflow

The repo already has a workflow at **`.github/workflows/deploy.yml`**. It runs on push to `main`/`master` and:

- Copies the repo to the VM under `/tmp/streamlit-app-deploy/`.
- Copies files into `/opt/streamlit-app/app/`, updates the venv, and restarts the `streamlit` service.

**Important:** The workflow copies the **root** of the repo into `/opt/streamlit-app/app/`. So either:

- Your repo root **is** the app (i.e. `app.py` and `requirements.txt` are at the root), or  
- You need to change the workflow so it copies the contents of the `app/` folder (e.g. the directory that contains `app.py`) into `/opt/streamlit-app/app/`.

After the first successful run, every push to `main`/`master` will update the app on the VM.

---

## Part 5: Useful Commands on the VM

```bash
# Restart the app
sudo systemctl restart streamlit

# Follow logs
sudo journalctl -u streamlit -f

# Stop the app
sudo systemctl stop streamlit

# Update code and restart (if not using CI/CD)
cd /opt/streamlit-app
git pull
cd app
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart streamlit
```

---

## Alternative: Upload Code Without Git

If you don’t use Git on the VM:

1. On your computer, zip the app folder (the one that contains `app.py` and `requirements.txt`).
2. From your computer (with `gcloud` installed and logged in):

```bash
gcloud compute scp app.zip EXTERNAL_IP:/opt/streamlit-app/ --zone=YOUR_ZONE
```

3. On the VM:

```bash
cd /opt/streamlit-app
unzip -o app.zip
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then create and start the `streamlit.service` as in **2.6**.

---

## Optional: Run the Setup Script

If you prefer a script to do most of the VM setup (after you’ve cloned the repo and confirmed the path):

```bash
cd /opt/streamlit-app/app
chmod +x setup-vm.sh
./setup-vm.sh
```

Then add credentials and fix the service `User=` if needed (script uses current user).

---

## Troubleshooting: 413 Payload Too Large on File Upload

If uploads fail with **AxiosError: Request failed with status code 413**:

1. **Streamlit limit** – The app’s `.streamlit/config.toml` sets `maxUploadSize = 600` (MB). If your repo has an older config, ensure it contains:
   ```toml
   [server]
   maxUploadSize = 600
   ```
   Then restart the service: `sudo systemctl restart streamlit`.

2. **Nginx (if you use it in front of Streamlit)** – Nginx’s default body limit is 1 MB. Increase it:
   ```bash
   sudo nano /etc/nginx/sites-available/streamlit
   ```
   Inside the `server { ... }` block add (e.g. 600MB to match Streamlit):
   ```nginx
   client_max_body_size 600M;
   ```
   Then:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Restart Streamlit** after any config change: `sudo systemctl restart streamlit`.

---

## Checklist Summary

- [ ] GCP project created, Compute Engine API enabled  
- [ ] VM created (e2-medium or similar), tag `streamlit-app`, External IP noted  
- [ ] Firewall rule `allow-streamlit` for TCP 8501  
- [ ] SSH’d into VM, installed Python/pip/git  
- [ ] Cloned repo to `/opt/streamlit-app`, venv and `pip install -r requirements.txt` in `app/`  
- [ ] Google Drive JSON in `/opt/streamlit-app/app/` (if used)  
- [ ] `streamlit.service` created and enabled, service started  
- [ ] App opens at `http://<EXTERNAL_IP>:8501`  
- [ ] (Optional) GitHub Secrets and deploy workflow configured for push-to-deploy  

For a printable checklist, see **GCP_SETUP_CHECKLIST.md** in this folder.
