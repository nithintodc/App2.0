#!/bin/bash
# Script to push app folder to GitHub repository
# Repository: https://github.com/nithintodc/App2.0.git

set -e

echo "🚀 Pushing to GitHub Repository"
echo "Repository: https://github.com/nithintodc/App2.0.git"
echo ""

cd /Users/nithi/Downloads/TODC/App2.0-cloud-app/app

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
else
    echo "✓ Git repository already initialized"
fi

# Check git config
if ! git config user.name > /dev/null 2>&1; then
    echo "⚙️  Configuring git..."
    read -p "Enter your name: " GIT_NAME
    read -p "Enter your email: " GIT_EMAIL
    git config user.name "$GIT_NAME"
    git config user.email "$GIT_EMAIL"
fi

# Add remote
echo ""
echo "🔗 Setting up remote..."
if git remote get-url origin > /dev/null 2>&1; then
    echo "Remote already exists, updating..."
    git remote set-url origin https://github.com/nithintodc/App2.0.git
else
    git remote add origin https://github.com/nithintodc/App2.0.git
fi
echo "✓ Remote configured"

# Add all files
echo ""
echo "➕ Adding files..."
git add .

# Check what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short

# Commit
echo ""
read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Initial commit: Streamlit cloud application"
fi

echo "💾 Committing..."
git commit -m "$COMMIT_MSG"
echo "✓ Committed"

# Determine branch name
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
if [ -z "$CURRENT_BRANCH" ]; then
    git branch -M main
    CURRENT_BRANCH="main"
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
echo "Branch: $CURRENT_BRANCH"
echo ""

if git push -u origin "$CURRENT_BRANCH"; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "Repository: https://github.com/nithintodc/App2.0"
    echo ""
    echo "Next steps:"
    echo "1. Verify files on GitHub"
    echo "2. Set up GitHub Secrets for CI/CD (see DEPLOYMENT_GUIDE.md)"
    echo "3. Test CI/CD by making a change and pushing"
else
    echo ""
    echo "❌ Push failed"
    echo ""
    echo "Common issues:"
    echo "- Authentication: You may need a Personal Access Token"
    echo "  Create one at: https://github.com/settings/tokens"
    echo "- Check your internet connection"
    echo ""
    exit 1
fi
