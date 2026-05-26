# InvoiceSnap

> **Turn PDF invoices into structured data instantly.**
>
> Drag, drop, extract. No manual entry. No signup. No storage.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Invoicesnap extracts vendor names, dates, amounts, tax, and line items from PDF invoices using AI. Works with any invoice format — no templates needed. Privacy-first: nothing is stored on disk.

<p align="center">
  <img src="https://img.shields.io/badge/status-MVP-brightgreen" alt="MVP">
  <img src="https://img.shields.io/badge/Product_Hunt-launching_soon-orange" alt="Product Hunt">
</p>

## ✨ Features

- **📄 Drag & Drop** — Upload any PDF invoice, get results instantly
- **🤖 AI-Powered** — DeepSeek/OpenAI extracts vendor, dates, totals, tax, line items
- **🔒 Privacy First** — Files processed in memory, never stored on disk
- **📊 Export** — Download results as CSV or Excel
- **🌐 Multi-Currency** — Auto-detects USD, EUR, GBP, and 50+ more
- **⚡ No-AI Fallback** — Rule-based extraction works without an API key
- **💳 Stripe Ready** — 3 free extractions, then $9/month Pro plan

## 🚀 Quick Start

```bash
# 1. Clone or navigate to the project
cd invoicesnap

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set up your AI key (optional — rule-based extraction works without it)
export OPENAI_API_KEY="sk-..."        # or DEEPSEEK_API_KEY

# 4. Start the server
./run.sh

# 5. Open http://localhost:8000
```

**Optional: Stripe payments**
```bash
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_PRICE_ID="price_..."
```

## 🏗️ Architecture

```
invoicesnap/
├── backend/
│   ├── main.py          # FastAPI app — routes, upload, export, Stripe
│   ├── extractor.py     # PDF text extraction + AI/rule-based parsing
│   ├── pricing.py       # Stripe checkout + usage tracking
│   └── requirements.txt
├── frontend/
│   └── index.html       # Complete SPA — landing, upload, results, export
├── run.sh               # Dev server launcher
├── .env.example         # Configuration template
└── README.md
```

### Extraction Pipeline

```
PDF Upload → PyMuPDF text extraction → Rule-based parsing
                                     → AI parsing (DeepSeek/OpenAI, optional)
                                     → Merge results (AI priority, rules fill gaps)
                                     → Return structured JSON
```

## 🔌 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/usage` | Free extractions remaining |
| `POST` | `/api/extract` | Upload PDF, get extracted data |
| `POST` | `/api/export` | Export results as CSV/XLSX |
| `POST` | `/api/create-checkout` | Create Stripe checkout session |

### Example: Extract

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "X-Session-Id: my-session" \
  -F "file=@invoice.pdf"
```

Response:
```json
{
  "vendor_name": "ACME Corp",
  "invoice_number": "INV-2026-0042",
  "invoice_date": "2026-05-20",
  "due_date": "2026-06-19",
  "total_amount": 8006.22,
  "currency": "USD",
  "tax_amount": 627.22,
  "line_items": [
    {
      "description": "Web Development Services",
      "quantity": 40,
      "unit_price": 150.00,
      "amount": 6000.00
    }
  ],
  "remaining_free": 2
}
```

## 🎨 Design

- Dark mode by default
- Brand color: `#2563eb` (blue)
- Stripe-inspired minimalism
- Mobile-responsive
- Inter font

## 📋 Product Hunt Launch Checklist

- [x] Working MVP with AI extraction
- [x] Clean landing page
- [x] Free tier (3 extractions)
- [x] Pro pricing ($9/mo via Stripe)
- [x] CSV/Excel export
- [x] Mobile responsive
- [ ] Demo video (placeholder ready)
- [ ] Custom domain
- [ ] PH launch assets (see `PRODUCT_HUNT.md`)

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, PyMuPDF, Stripe
- **AI:** DeepSeek / OpenAI (configurable)
- **Frontend:** Vanilla HTML/CSS/JS (no framework)
- **Design:** Custom dark theme, Inter font

## 📄 License

MIT — see [LICENSE](LICENSE)

---

Built with ❤️ for Product Hunt. [@invoicesnap](https://twitter.com/invoicesnap)
