# Streamlit Cloud Setup Guide

This guide explains how to deploy your app to Streamlit Cloud and configure Google Drive credentials.

---

## ⚠️ "Credentials not found" in production

If you see **"Service account credentials not found at: .../todc-marketing-....json"** on Streamlit Cloud:

1. Open your app on [share.streamlit.io](https://share.streamlit.io) → click **⋮** (three dots) → **Settings**.
2. Scroll to **Secrets** and click **Edit** (or **Open in editor**).
3. Paste your GCP service account in **TOML** form. You need both section headers and all keys from your JSON:

```toml
[gcp]
[gcp.service_account]
type = "service_account"
project_id = "your-actual-project-id"
private_key_id = "your-actual-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
paste every line of the key here
-----END PRIVATE KEY-----"""
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"
```

4. Copy each value from your **downloaded JSON key** (from Google Cloud Console → IAM → Service accounts → Keys).
5. Use **triple quotes** `"""` around `private_key` and keep the newlines inside it.
6. Save. The app will redeploy; reload the app page.

---

## 🚀 Deploy to Streamlit Cloud

### Step 1: Push Code to GitHub

1. Make sure your code is pushed to GitHub:
   ```bash
   cd /Users/nithi/Downloads/TODC/App2.0-cloud-app/app
   git add .
   git commit -m "Ready for Streamlit Cloud"
   git push origin main
   ```

2. Verify your repository is on GitHub: https://github.com/nithintodc/App2.0

### Step 2: Connect to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Fill in the details:
   - **Repository**: Select `nithintodc/App2.0`
   - **Branch**: `main` (or `master`)
   - **Main file path**: `app.py`
   - **App URL**: Choose your custom subdomain (optional)
5. Click **"Deploy"**

### Step 3: Add Google Drive Credentials (Secrets)

Streamlit Cloud uses **Secrets** instead of files for credentials.

#### Option A: Using Streamlit Cloud Dashboard

1. In your Streamlit Cloud app dashboard, click **"⋮"** (three dots) → **"Settings"**
2. Scroll down to **"Secrets"** section
3. Click **"Edit secrets"** or **"Add secret"**
4. Add your Google Drive service account credentials in TOML format:

```toml
[gcp]
[gcp.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project-id.iam.gserviceaccount.com"
```

#### Option B: Using secrets.toml File (Alternative)

1. Create a `.streamlit/secrets.toml` file in your repository (for local testing)
2. Add the same TOML format as above
3. **IMPORTANT**: Add `.streamlit/secrets.toml` to `.gitignore` (already done)
4. For Streamlit Cloud, use the dashboard method (Option A)

### Step 4: Get Your Service Account JSON

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Click on your service account
4. Go to **"Keys"** tab
5. Click **"Add Key"** → **"Create new key"**
6. Select **JSON** format
7. Download the JSON file

### Step 5: Convert JSON to TOML Format

Your downloaded JSON file looks like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

Convert it to TOML format for Streamlit secrets:

```toml
[gcp]
[gcp.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
Your private key here (keep the newlines)
-----END PRIVATE KEY-----"""
client_email = "your-service-account@project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project-id.iam.gserviceaccount.com"
```

**Important Notes:**
- Use triple quotes `"""` for the `private_key` field to preserve newlines
- Copy all values exactly from your JSON file
- Keep the `[gcp]` and `[gcp.service_account]` section headers

### Step 6: Paste into Streamlit Cloud Secrets

1. Copy the entire TOML format above
2. Paste it into Streamlit Cloud Secrets editor
3. Click **"Save"**

### Step 7: Verify Deployment

1. Go back to your Streamlit Cloud app
2. The app should automatically redeploy
3. Test the export functionality:
   - Upload files
   - Go to Dashboard
   - Click "Export All Tables to Excel"
   - Check if Google Drive upload works

## 🔍 Troubleshooting

### Error: "Service account credentials not found"

**Solution:**
- Verify secrets are added in Streamlit Cloud dashboard
- Check the TOML format is correct
- Ensure all fields from JSON are included

### Error: "Shared drive not found"

**Solution:**
1. Verify the service account email has access to "Data-Analysis-Uploads" drive
2. Check the drive name matches exactly: "Data-Analysis-Uploads"
3. Ensure service account has "Content Manager" or "Editor" role

### Error: "Invalid credentials"

**Solution:**
- Verify private_key has proper newlines (use triple quotes in TOML)
- Check all fields are copied correctly from JSON
- Ensure no extra spaces or characters

### App not deploying

**Solution:**
- Check GitHub repository is connected
- Verify `app.py` is in the root of the repository
- Check deployment logs in Streamlit Cloud dashboard

## 📝 Quick Reference

| Item | Value |
|------|-------|
| **Secrets Location** | Streamlit Cloud Dashboard → Settings → Secrets |
| **Format** | TOML |
| **Section** | `[gcp.service_account]` |
| **Private Key** | Use triple quotes `"""` to preserve newlines |
| **Main File** | `app.py` |

## ✅ Checklist

- [ ] Code pushed to GitHub
- [ ] App deployed on Streamlit Cloud
- [ ] Service account JSON downloaded
- [ ] JSON converted to TOML format
- [ ] Secrets added to Streamlit Cloud
- [ ] Google Drive shared with service account
- [ ] Export functionality tested
- [ ] Google Drive upload verified

## 🎯 Summary

1. **Deploy app** to Streamlit Cloud from GitHub
2. **Get service account JSON** from Google Cloud Console
3. **Convert JSON to TOML** format
4. **Add secrets** in Streamlit Cloud dashboard
5. **Test** export functionality

Your app will now work on Streamlit Cloud with Google Drive integration!
