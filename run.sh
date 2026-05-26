#!/bin/bash
# InvoiceSnap — Start dev server
set -e

cd "$(dirname "$0")"

# Check Python
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install -r backend/requirements.txt
}

echo "🚀 Starting InvoiceSnap on http://localhost:8000"
echo "   Set OPENAI_API_KEY (or DEEPSEEK_API_KEY) for AI extraction"
echo "   Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID for payments"
echo ""

cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
