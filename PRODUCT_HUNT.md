# InvoiceSnap — Product Hunt Launch Materials

## 🎯 Tagline (60 chars max)
> **Turn any PDF invoice into structured data in seconds. No templates, no manual entry.**

## 📝 Description
InvoiceSnap is the fastest way to extract data from PDF invoices. Upload any invoice — from any vendor, in any format — and get vendor name, dates, line items, totals, and tax extracted automatically.

**Why we built it:**
Every accountant, freelancer, and small business owner knows the pain of manually typing invoice data into spreadsheets or accounting software. Existing tools are expensive, complex, or require template setup. We wanted something that just works — drag, drop, done.

**How it works:**
1. Upload a PDF invoice (or drag & drop)
2. AI extracts all fields: vendor, invoice #, dates, line items, tax, total
3. Review the results in a clean table
4. Export as CSV or Excel

**Key features:**
- 🔒 Privacy-first: nothing is stored on disk
- 🤖 AI-powered extraction (DeepSeek/OpenAI)
- ⚡ Works without AI too — built-in rule-based fallback
- 💰 3 free extractions, then $9/month
- 🌐 Multi-currency support (USD, EUR, GBP, 50+)
- 📊 CSV & Excel export

**Tech:** Python/FastAPI backend, vanilla JS frontend, PyMuPDF for PDF parsing.

## 💬 First Comment

Hey Product Hunt! 👋

I'm the maker of InvoiceSnap. I built this because I was tired of manually copying invoice data into spreadsheets every month. Turns out, a lot of people have the same frustration.

**A few things I'd love feedback on:**
1. What invoice formats break the extraction? (Send me examples!)
2. Is the pricing right? ($9/mo for unlimited)
3. What integrations would you want? (QuickBooks, Xero, Zapier?)

**Behind the scenes:**
- Built in ~2 days as an MVP
- Python/FastAPI backend, vanilla JS frontend
- Uses PyMuPDF for text extraction + DeepSeek for AI parsing
- Rule-based fallback works without any API key

**What's next:**
- Batch upload (multiple invoices at once)
- QuickBooks/Xero export
- Receipt support (images + OCR)
- API for developers

Try it out and let me know what you think! Happy to answer any questions.

## 🖼️ Media Assets

### Screenshots needed:
1. **Hero + Upload** — The landing page with drag-and-drop zone
2. **Results View** — Extracted invoice data in the summary grid + line items table
3. **Export** — CSV/Excel download in action
4. **Mobile View** — Responsive design on phone

### Demo Video Script (30-60 seconds):
1. Show landing page (5s)
2. Drag an invoice PDF onto the upload zone (5s)
3. Results appear — highlight vendor, dates, total, line items (15s)
4. Click "Export CSV" — show downloaded file (10s)
5. Show pricing page — "3 free, then $9/mo" (5s)
6. End with "InvoiceSnap — try it free" (5s)

## 📊 Pricing
| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 3 extractions, all field types, CSV/Excel export |
| **Pro** | $9/mo | Unlimited extractions, priority processing, API access |

## 🔗 Links
- **Website:** https://invoicesnap.app (coming soon)
- **Twitter:** @invoicesnap
- **Email:** hello@invoicesnap.app

## 🎯 Target Audience
- Freelancers tracking client invoices
- Small business owners doing their own bookkeeping
- Accountants processing client invoices
- Anyone who receives PDF invoices and needs the data in a spreadsheet

## 🏷️ Tags
`invoice`, `pdf`, `data-extraction`, `ai`, `productivity`, `finance`, `accounting`, `freelancers`, `open-source`
