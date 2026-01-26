#!/bin/bash
# Quick script to push app to GitHub
# Run this script from the project root directory

set -e

echo "🚀 GitHub Push Script"
echo "===================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📦 Initializing git repository...${NC}"
    git init
else
    echo -e "${GREEN}✓ Git repository already initialized${NC}"
fi

# Check git config
if ! git config user.name > /dev/null 2>&1; then
    echo -e "${YELLOW}⚙️  Git user not configured${NC}"
    read -p "Enter your name: " GIT_NAME
    read -p "Enter your email: " GIT_EMAIL
    git config user.name "$GIT_NAME"
    git config user.email "$GIT_EMAIL"
fi

echo ""
echo -e "${YELLOW}📋 Checking files to commit...${NC}"
git status --short

echo ""
read -p "Do you want to proceed with adding all files? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Cancelled${NC}"
    exit 1
fi

# Add all files
echo -e "${YELLOW}➕ Adding files...${NC}"
git add .

# Check for sensitive files
echo -e "${YELLOW}🔍 Checking for sensitive files...${NC}"
if git diff --cached --name-only | grep -E "\.json$" | grep -v "package.json\|package-lock.json"; then
    echo -e "${RED}⚠️  WARNING: JSON files detected!${NC}"
    echo "Make sure credentials are in .gitignore"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Cancelled${NC}"
        exit 1
    fi
fi

# Commit
echo -e "${YELLOW}💾 Committing changes...${NC}"
read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Initial commit: Streamlit cloud application with CI/CD"
fi

git commit -m "$COMMIT_MSG"
echo -e "${GREEN}✓ Committed${NC}"

# Check for remote
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo -e "${YELLOW}🔗 No remote repository configured${NC}"
    echo "Please add your GitHub repository URL:"
    echo "Example: https://github.com/username/repo-name.git"
    read -p "Enter repository URL: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo -e "${RED}❌ No URL provided. Exiting.${NC}"
        echo "Run manually: git remote add origin YOUR_REPO_URL"
        exit 1
    fi
    
    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✓ Remote added${NC}"
else
    echo -e "${GREEN}✓ Remote already configured${NC}"
    git remote -v
fi

# Determine branch name
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
if [ -z "$CURRENT_BRANCH" ]; then
    CURRENT_BRANCH="main"
fi

echo ""
echo -e "${YELLOW}📤 Pushing to GitHub...${NC}"
echo "Branch: $CURRENT_BRANCH"

# Push
if git push -u origin "$CURRENT_BRANCH" 2>&1 | tee /tmp/git_push.log; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Go to your GitHub repository"
    echo "2. Verify all files are there"
    echo "3. Set up GitHub Secrets for CI/CD (see DEPLOYMENT_GUIDE.md)"
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    echo ""
    echo "Common issues:"
    echo "- Authentication: Use Personal Access Token for HTTPS"
    echo "- Remote URL: Check with 'git remote -v'"
    echo "- Branch name: Current branch is '$CURRENT_BRANCH'"
    echo ""
    echo "Check the error message above for details"
    exit 1
fi
