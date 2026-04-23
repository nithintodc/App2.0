#!/bin/bash
# Run Python App with Virtual Environment
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
echo "Home: http://localhost:8501/"
echo "New:  http://localhost:8501/new"
streamlit run app.py
