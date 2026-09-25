#!/bin/bash
# Retentia - Investor Pitch Setup Script
# Run this script before the meeting to ensure everything is perfect.

echo "⚡ Starting Retentia Setup for Investor Pitch..."
echo "================================================="

# 1. Ensure dependencies are installed
echo "[1/4] Checking dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "✅ Dependencies ready."

# 2. Check Database Status
echo "[2/4] Verifying database connection..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  No DATABASE_URL found in environment. The app will automatically use the Offline Demo Mode (SQLite)."
else
    echo "✅ Live database URL detected."
fi

# 3. Check AI API Key
echo "[3/4] Verifying GenAI keys..."
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  No GEMINI_API_KEY found. The app will use high-quality simulated AI responses for the pitch."
else
    echo "✅ Gemini AI Key detected."
fi

# 4. Launch the application
echo "[4/4] Launching Retentia Enterprise OS..."
echo "================================================="
echo "The app will open in your browser automatically."
echo "Press Ctrl+C to stop the server after the pitch."
echo ""
streamlit run app.py
