# Delivery Platform Data Analysis - Cloud Application

A modern Streamlit-based cloud application for analyzing DoorDash and UberEats delivery platform data with automated reporting and Google Drive integration.

## 🚀 Features

- **Multi-Screen Interface**: Clean, SaaS-style UI with file upload and dashboard screens
- **Batch File Intake**: Upload the four reporting CSVs together with automatic filename mapping
- **Date Range Configuration**: Configure Pre/Post periods with automatic last-year calculations
- **Comprehensive Analysis**: 
  - Store-level and platform-level analytics
  - Combined DoorDash + UberEats analysis
  - Corporate vs TODC marketing analysis
  - Year-over-year comparisons
- **Google Drive Integration**: Automatic export to Google Drive
- **CI/CD Ready**: Automated deployment with GitHub Actions

## 📋 Requirements

- Python 3.8+
- Google Cloud Platform account (for deployment)
- Google Drive service account credentials

## 🛠️ Local Development

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd App2.0-cloud-app
```

2. Navigate to app directory:
```bash
cd app
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Add Google Drive credentials:
   - Place your `todc-marketing-*.json` service account file in the `app/` directory

### Running Locally

```bash
cd app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## ☁️ Deployment

### Quick Start
See **[QUICK_START_DEPLOYMENT.md](QUICK_START_DEPLOYMENT.md)** for a 15-minute deployment guide.

### Full Guide
See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for comprehensive deployment instructions.

### Setup Checklist
Use **[GCP_SETUP_CHECKLIST.md](GCP_SETUP_CHECKLIST.md)** to track your deployment progress.

## 📁 Project Structure

```
App2.0-cloud-app/
├── app/
│   ├── app.py                 # Main application entry point
│   ├── config.py              # Configuration settings
│   ├── data_loading.py        # Data loading functions
│   ├── data_processing.py     # Data processing logic
│   ├── file_upload_screen.py  # File upload UI
│   ├── marketing_analysis.py   # Marketing data analysis
│   ├── table_generation.py    # Table generation functions
│   ├── ui_components.py      # UI components
│   ├── export_functions.py   # Export functionality
│   ├── gdrive_utils.py       # Google Drive utilities
│   └── requirements.txt       # Python dependencies
├── .github/
│   └── workflows/
│       └── deploy.yml        # GitHub Actions CI/CD workflow
├── DEPLOYMENT_GUIDE.md       # Full deployment guide
├── QUICK_START_DEPLOYMENT.md # Quick deployment guide
├── GCP_SETUP_CHECKLIST.md    # Deployment checklist
└── setup-vm.sh               # VM setup script
```

## 🔧 Configuration

### Google Drive Setup

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create a service account
4. Download JSON credentials
5. Place credentials file in `app/` directory as `todc-marketing-*.json`

### Environment Variables

No environment variables required for basic operation. All configuration is handled through the UI.

## 📊 Usage

### Step 1: Upload Files
1. Enter Pre and Post date ranges
2. Review the suggested download range
3. Upload the four CSVs in one batch
4. The app maps files automatically:
   - `FINANCIAL*` -> DoorDash Financial
   - `MARKETING_PROMO*` -> DoorDash Promo
   - `MARKETING_SPONSORED*` -> DoorDash Ads
   - Everything else -> UberEats Financial

### Step 2: Run Analysis
1. Click "Run Analysis"
2. View dashboard with comprehensive analytics
3. Select stores to analyze
4. Export results to Excel (automatically uploaded to Google Drive)

## 🔄 CI/CD

The application includes GitHub Actions workflow for automated deployment:

- **Automatic deployment** on push to main/master branch
- **Zero-downtime updates** with service restart
- **Backup creation** before each deployment
- **Dependency updates** automatically installed

See `.github/workflows/deploy.yml` for workflow configuration.

## 🛡️ Security

- Service account credentials are never committed to Git
- Firewall rules restrict access to necessary ports
- All sensitive files are in `.gitignore`
- HTTPS recommended for production (see deployment guide)

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

For deployment issues:
1. Check deployment guides
2. Review GitHub Actions logs
3. Check VM system logs: `sudo journalctl -u streamlit -f`

## 🎯 Roadmap

- [ ] Custom domain support
- [ ] SSL/HTTPS configuration
- [ ] Enhanced monitoring
- [ ] Automated backups
- [ ] Multi-user support
