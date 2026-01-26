# Guide: Push App to GitHub Repository

Follow these steps to push your Streamlit app to GitHub.

## Prerequisites

- GitHub account
- Git installed on your computer
- Terminal/Command Prompt access

---

## Step 1: Create GitHub Repository

### Option A: Create via GitHub Website

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in the details:
   - **Repository name**: `streamlit-analysis-app` (or your preferred name)
   - **Description**: "Cloud-based Streamlit app for delivery platform data analysis"
   - **Visibility**: 
     - ✅ **Public** (free, anyone can see)
     - ✅ **Private** (only you can see, requires GitHub Pro for free private repos)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

### Option B: Create via GitHub CLI (if installed)

```bash
gh repo create streamlit-analysis-app --public --description "Cloud-based Streamlit app for delivery platform data analysis"
```

---

## Step 2: Initialize Git (if not already done)

Open Terminal/Command Prompt and navigate to your project:

```bash
cd /Users/nithi/Downloads/TODC/App2.0-cloud-app
```

Check if git is initialized:

```bash
git status
```

If you see "fatal: not a git repository", initialize it:

```bash
git init
```

---

## Step 3: Configure Git (if first time)

Set your name and email (if not already configured globally):

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

Or set globally for all repositories:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 4: Add All Files

Add all files to git staging:

```bash
git add .
```

Verify what will be committed:

```bash
git status
```

You should see all your files listed. Make sure sensitive files (like `*.json` credentials) are NOT listed (they should be in `.gitignore`).

---

## Step 5: Create Initial Commit

Commit all files:

```bash
git commit -m "Initial commit: Streamlit cloud application with CI/CD"
```

---

## Step 6: Add GitHub Remote

Add your GitHub repository as the remote origin. Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual values:

### If using HTTPS:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### If using SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
```

**To find your repository URL:**
- Go to your GitHub repository page
- Click the green **"Code"** button
- Copy the URL shown (HTTPS or SSH)

---

## Step 7: Verify Remote

Check that the remote was added correctly:

```bash
git remote -v
```

You should see:
```
origin  https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git (fetch)
origin  https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git (push)
```

---

## Step 8: Push to GitHub

Push your code to GitHub:

```bash
git branch -M main
git push -u origin main
```

**Note:** If your default branch is `master` instead of `main`:

```bash
git branch -M master
git push -u origin master
```

**If prompted for credentials:**
- **HTTPS**: Enter your GitHub username and Personal Access Token (not password)
- **SSH**: Should work automatically if you have SSH keys set up

---

## Step 9: Verify on GitHub

1. Go to your GitHub repository page
2. Refresh the page
3. You should see all your files
4. Check that `.github/workflows/deploy.yml` exists (for CI/CD)

---

## Troubleshooting

### Issue: "Authentication failed"

**Solution for HTTPS:**
1. GitHub no longer accepts passwords for HTTPS
2. Create a Personal Access Token:
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token
   - Select scopes: `repo` (full control)
   - Copy the token
3. Use the token as your password when pushing

**Solution for SSH:**
1. Generate SSH key if you don't have one:
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```
2. Add to GitHub:
   - Copy public key: `cat ~/.ssh/id_ed25519.pub`
   - GitHub → Settings → SSH and GPG keys → New SSH key
   - Paste and save

### Issue: "Remote origin already exists"

If you already have a remote:

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### Issue: "Failed to push some refs"

If GitHub repo has files you don't have locally:

```bash
git pull origin main --allow-unrelated-histories
# Resolve any conflicts if prompted
git push -u origin main
```

### Issue: Credentials file showing in git status

Make sure `.gitignore` includes:
```
*.json
!package.json
app/todc-marketing-*.json
```

Then remove from git (if already added):

```bash
git rm --cached app/todc-marketing-*.json
git commit -m "Remove credentials from tracking"
```

---

## Quick Command Summary

```bash
# Navigate to project
cd /Users/nithi/Downloads/TODC/App2.0-cloud-app

# Initialize git (if needed)
git init

# Configure git (if first time)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Commit
git commit -m "Initial commit: Streamlit cloud application with CI/CD"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Next Steps After Pushing

1. **Set up GitHub Secrets** for CI/CD (see DEPLOYMENT_GUIDE.md)
2. **Test CI/CD** by making a small change and pushing
3. **Deploy to GCP** following QUICK_START_DEPLOYMENT.md

---

## Making Future Changes

After your initial push, for future updates:

```bash
# Make your changes to files
git add .
git commit -m "Description of your changes"
git push
```

The CI/CD workflow will automatically deploy changes to your GCP VM!
