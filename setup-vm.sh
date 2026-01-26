#!/bin/bash
# VM Setup Script for Streamlit App
# Run this script on your GCP Compute Engine VM after initial SSH

set -e

echo "🚀 Starting Streamlit App VM Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt-get install -y python3 python3-pip python3-venv git nginx supervisor

# Get current user
CURRENT_USER=$(whoami)
echo -e "${GREEN}✓ Current user: $CURRENT_USER${NC}"

# Create app directory
echo -e "${YELLOW}📁 Creating application directory...${NC}"
sudo mkdir -p /opt/streamlit-app/app
sudo chown -R $CURRENT_USER:$CURRENT_USER /opt/streamlit-app
cd /opt/streamlit-app

# Check if repo is already cloned
if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Repository already exists, pulling latest...${NC}"
    git pull
else
    echo -e "${YELLOW}📥 Please clone your repository:${NC}"
    echo "   cd /opt/streamlit-app"
    echo "   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
    read -p "Press Enter after cloning the repository..."
fi

# Setup Python environment
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
cd /opt/streamlit-app/app

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python environment ready${NC}"

# Create systemd service
echo -e "${YELLOW}⚙️  Creating systemd service...${NC}"
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit App
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=/opt/streamlit-app/app
Environment="PATH=/opt/streamlit-app/app/venv/bin"
ExecStart=/opt/streamlit-app/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo -e "${YELLOW}🔄 Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

# Check status
echo -e "${YELLOW}📊 Service status:${NC}"
sudo systemctl status streamlit --no-pager | head -15

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Upload your Google Drive credentials JSON to /opt/streamlit-app/app/"
echo "   2. Verify the app is running: sudo systemctl status streamlit"
echo "   3. Check logs: sudo journalctl -u streamlit -f"
echo "   4. Access your app at: http://$(curl -s ifconfig.me):8501"
echo ""
