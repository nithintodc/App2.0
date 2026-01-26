# Quick Start: Add Credentials to Streamlit Cloud

## 🎯 Quick Steps

### 1. Get Your Service Account JSON

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **IAM & Admin** → **Service Accounts** → Select your service account
3. **Keys** tab → **Add Key** → **Create new key** → **JSON**
4. Download the JSON file

### 2. Open Your JSON File

Open the downloaded JSON file and copy these values:
- `type`
- `project_id`
- `private_key_id`
- `private_key` (entire key including BEGIN/END lines)
- `client_email`
- `client_id`
- `auth_uri`
- `token_uri`
- `auth_provider_x509_cert_url`
- `client_x509_cert_url`

### 3. Add to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Select your app
3. Click **"⋮"** (three dots) → **"Settings"**
4. Scroll to **"Secrets"** section
5. Click **"Edit secrets"**
6. Paste this template and fill in your values:

```toml
[gcp]
[gcp.service_account]
type = "service_account"
project_id = "PASTE_YOUR_PROJECT_ID"
private_key_id = "PASTE_YOUR_PRIVATE_KEY_ID"
private_key = """-----BEGIN PRIVATE KEY-----
PASTE_YOUR_ENTIRE_PRIVATE_KEY_HERE
INCLUDE_ALL_LINES
-----END PRIVATE KEY-----"""
client_email = "PASTE_YOUR_CLIENT_EMAIL"
client_id = "PASTE_YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "PASTE_YOUR_CLIENT_X509_CERT_URL"
```

7. Click **"Save"**
8. App will automatically redeploy

### 4. Share Google Drive

1. From the JSON file, copy the `client_email` value
2. Go to Google Drive
3. Find or create shared drive: **"Data-Analysis-Uploads"**
4. Right-click → **Share** → Paste the email
5. Grant role: **Content Manager**
6. Click **Send**

### 5. Test

1. Go to your Streamlit Cloud app
2. Upload files and test export
3. Check if Google Drive upload works

## ✅ Done!

Your credentials are now configured for Streamlit Cloud.

## 📋 Example

If your JSON has:
```json
{
  "type": "service_account",
  "project_id": "my-project-123",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----\n",
  "client_email": "my-service@my-project.iam.gserviceaccount.com"
}
```

Your TOML should be:
```toml
[gcp]
[gcp.service_account]
type = "service_account"
project_id = "my-project-123"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQ...
-----END PRIVATE KEY-----"""
client_email = "my-service@my-project.iam.gserviceaccount.com"
```

**Key Points:**
- Use `"""` triple quotes for `private_key` to preserve newlines
- Copy all values exactly from JSON
- Keep the section headers `[gcp]` and `[gcp.service_account]`
