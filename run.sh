#!/bin/bash
# Run Python App with Virtual Environment
# Recreate venv if missing or broken (e.g. Homebrew Python was upgraded/removed)
if [ ! -d "venv" ] || [ ! -e "venv/bin/python" ] || ! venv/bin/python -c "import sys" 2>/dev/null; then
  echo "Creating virtual environment..."
  rm -rf venv
  python3 -m venv venv
fi
source venv/bin/activate
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
echo "Home: http://localhost:8501/"
echo "New:  http://localhost:8501/new"
streamlit run app.py
