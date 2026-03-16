#!/usr/bin/env bash
# ── deploy.sh ── Deploy TODC Analytics to a GCP Compute Engine VM
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated  (gcloud auth login)
#   2. The VM already exists with Python 3, venv, and a systemd service "streamlit"
#      (see GCP_VM_DEPLOY_GUIDE.md for first-time setup)
#
# Usage:
#   ./deploy.sh                          # uses defaults below
#   ./deploy.sh --vm myvm --zone us-central1-a --user nithin
#
# What it does:
#   - Copies all app files to the VM via gcloud scp
#   - Installs/updates Python dependencies
#   - Restarts the streamlit systemd service
set -e

# ── Defaults (edit these or pass as flags) ──
VM_NAME="${GCP_VM_NAME:-todc-apps}"
VM_ZONE="${GCP_VM_ZONE:-us-central1-a}"
VM_USER="${GCP_VM_USER:-nithin}"
APP_DIR="/opt/streamlit-app/App2.0"

# ── Parse flags ──
while [[ $# -gt 0 ]]; do
    case "$1" in
        --vm)   VM_NAME="$2"; shift 2;;
        --zone) VM_ZONE="$2"; shift 2;;
        --user) VM_USER="$2"; shift 2;;
        --dir)  APP_DIR="$2"; shift 2;;
        *)      echo "Unknown flag: $1"; exit 1;;
    esac
done

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== TODC Analytics Deploy ==="
echo "  VM:   ${VM_USER}@${VM_NAME} (${VM_ZONE})"
echo "  Dir:  ${APP_DIR}"
echo ""

# 1. Copy files to a temp location on the VM
echo "[1/4] Uploading files to VM..."
gcloud compute scp --recurse --zone="${VM_ZONE}" \
    "${REPO_DIR}/"*.py \
    "${REPO_DIR}/requirements.txt" \
    "${REPO_DIR}/info.txt" \
    "${VM_USER}@${VM_NAME}:/tmp/todc-deploy/"

# Copy .streamlit folder
gcloud compute scp --recurse --zone="${VM_ZONE}" \
    "${REPO_DIR}/.streamlit" \
    "${VM_USER}@${VM_NAME}:/tmp/todc-deploy/.streamlit"

# Copy credentials JSON if present (not committed to git)
if ls "${REPO_DIR}"/todc-marketing-*.json 1>/dev/null 2>&1; then
    gcloud compute scp --zone="${VM_ZONE}" \
        "${REPO_DIR}"/todc-marketing-*.json \
        "${VM_USER}@${VM_NAME}:/tmp/todc-deploy/"
    echo "  (credentials JSON included)"
fi

# 2. Deploy on VM
echo "[2/4] Deploying on VM..."
gcloud compute ssh "${VM_USER}@${VM_NAME}" --zone="${VM_ZONE}" --command="
    set -e

    # Backup current app
    sudo cp -r ${APP_DIR} ${APP_DIR}-backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

    # Stop service
    sudo systemctl stop streamlit 2>/dev/null || true

    # Copy new files
    sudo cp /tmp/todc-deploy/*.py ${APP_DIR}/
    sudo cp /tmp/todc-deploy/requirements.txt ${APP_DIR}/
    sudo cp /tmp/todc-deploy/info.txt ${APP_DIR}/ 2>/dev/null || true
    sudo cp -r /tmp/todc-deploy/.streamlit ${APP_DIR}/ 2>/dev/null || true

    # Copy credentials if present
    if ls /tmp/todc-deploy/todc-marketing-*.json 1>/dev/null 2>&1; then
        sudo cp /tmp/todc-deploy/todc-marketing-*.json ${APP_DIR}/
    fi

    sudo chown -R ${VM_USER}:${VM_USER} ${APP_DIR}
"

# 3. Install deps & restart
echo "[3/4] Installing dependencies & restarting..."
gcloud compute ssh "${VM_USER}@${VM_NAME}" --zone="${VM_ZONE}" --command="
    set -e
    cd ${APP_DIR}

    # Create venv if missing
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    # Restart
    sudo systemctl daemon-reload
    sudo systemctl start streamlit
"

# 4. Verify
echo "[4/4] Verifying..."
gcloud compute ssh "${VM_USER}@${VM_NAME}" --zone="${VM_ZONE}" --command="
    sudo systemctl status streamlit --no-pager | head -15
"

# Cleanup temp files
gcloud compute ssh "${VM_USER}@${VM_NAME}" --zone="${VM_ZONE}" --command="
    rm -rf /tmp/todc-deploy
" 2>/dev/null || true

echo ""
echo "Done! App should be live at http://\$(gcloud compute instances describe ${VM_NAME} --zone=${VM_ZONE} --format='get(networkInterfaces[0].accessConfigs[0].natIP)'):8501"
