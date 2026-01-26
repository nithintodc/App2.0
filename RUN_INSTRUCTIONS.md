# How to Run the Cloud Application

## Prerequisites

1. **Python 3.8 or higher** installed on your system
2. **Google Drive Service Account credentials** - The file `app/todc-marketing-ad02212d4f16.json` should already be present

## Step-by-Step Instructions

### 1. Navigate to the App Directory

Open your terminal/command prompt and navigate to the app directory:

```bash
cd /Users/nithi/Downloads/TODC/App2.0-cloud-app/app
```

Or if you're already in the project root:
```bash
cd app
```

### 2. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

Or if you're using Python 3 specifically:
```bash
python3 -m pip install -r requirements.txt
```

This will install:
- streamlit
- pandas
- openpyxl
- google-api-python-client
- google-auth
- google-auth-httplib2

### 3. Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Or with Python 3:
```bash
python3 -m streamlit run app.py
```

### 4. Access the Application

After running the command, Streamlit will:
- Start a local web server
- Automatically open your default web browser
- Display the application at `http://localhost:8501`

If the browser doesn't open automatically, you can manually navigate to:
- **Local URL**: `http://localhost:8501`
- **Network URL**: Will be shown in the terminal (for access from other devices on your network)

## Using the Application

### Screen 1: Upload Files

1. **Upload DoorDash Data**: Click "Browse files" and select your `dd-data.csv` file
2. **Upload UberEats Data**: Click "Browse files" and select your `ue-data.csv` file
3. **Upload Marketing Folder**: 
   - Create a ZIP file containing your `marketing_*` folder(s)
   - Upload the ZIP file
4. **Enter Date Ranges**:
   - Pre Period: Format `MM/DD/YYYY-MM/DD/YYYY` (e.g., `11/1/2025-11/30/2025`)
   - Post Period: Format `MM/DD/YYYY-MM/DD/YYYY` (e.g., `12/1/2025-12/31/2025`)
5. **Click "Confirm and Run Analysis"** to proceed to the dashboard

### Screen 2: Dashboard

- View analysis results
- Select stores from the sidebar
- Export data to Excel (automatically uploaded to Google Drive in `cloud-app-uploads/outputs/` folder)

## Troubleshooting

### Port Already in Use

If you see an error about port 8501 being in use:

```bash
streamlit run app.py --server.port 8502
```

### Module Not Found Errors

Make sure you're in the `app` directory when running the command, or install dependencies again:

```bash
pip install -r requirements.txt
```

### Google Drive Upload Issues

- Ensure `app/todc-marketing-ad02212d4f16.json` exists
- Verify the service account has access to the Google Drive shared drive "Data-Analysis-Uploads"
- Check that the shared drive "Data-Analysis-Uploads" exists and the service account has permissions

### File Upload Issues

- Ensure CSV files are properly formatted
- Marketing ZIP should contain folders starting with `marketing_`
- Each marketing folder should contain `MARKETING_PROMOTION*.csv` and `MARKETING_SPONSORED_LISTING*.csv` files

## Stopping the Application

To stop the application:
- Press `Ctrl+C` in the terminal where Streamlit is running
- Or close the terminal window

## Quick Start Command

If you're already in the app directory, you can run everything with:

```bash
pip install -r requirements.txt && streamlit run app.py
```
