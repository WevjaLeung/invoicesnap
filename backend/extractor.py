"""
InvoiceSnap — PDF extraction + AI parsing.

Pipeline:
1. Extract raw text from PDF using PyMuPDF (fitz)
2. Rule-based extraction for common invoice patterns (always runs)
3. AI-powered extraction for better accuracy (when API key available)
4. Merge results: AI takes priority, rules fill gaps
"""

import json
import os
import re
from datetime import datetime, date
from typing import Optional
from decimal import Decimal, InvalidOperation

import fitz  # PyMuPDF

# AI provider config — use environment variables
AI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
AI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.environ.get("AI_MODEL", "deepseek-chat")


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            text_parts.append(text.strip())
    doc.close()
    return "\n\n".join(text_parts)


# ============================================================================
# Rule-based extraction (no AI needed)
# ============================================================================

_CURRENCY_MAP = {
    "$": "USD", "US$": "USD", "USD": "USD",
    "€": "EUR", "EUR": "EUR",
    "£": "GBP", "GBP": "GBP",
    "¥": "JPY", "JPY": "JPY",
    "₹": "INR", "INR": "INR",
    "₩": "KRW", "KRW": "KRW",
    "A$": "AUD", "AUD": "AUD",
    "C$": "CAD", "CAD": "CAD",
    "CHF": "CHF",
    "R$": "BRL", "BRL": "BRL",
    "HK$": "HKD", "HKD": "HKD",
    "S$": "SGD", "SGD": "SGD",
    "kr": "SEK",
}


def _detect_currency(text: str) -> str:
    """Detect currency from text symbols."""
    for symbol, code in _CURRENCY_MAP.items():
        if symbol in text:
            return code
    return "USD"


def _parse_amount(s: str) -> Optional[float]:
    """Parse a dollar amount string to float. Handles $1,234.56  1.234,56 etc."""
    if not s:
        return None
    s = s.strip()
    # Remove currency symbols
    s = re.sub(r'[\$\€\£\¥\₹\₩]', '', s)
    s = s.replace(' ', '').replace('\xa0', '')
    # Detect European format (1.234,56) vs US format (1,234.56)
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            # European: 1.234,56
            s = s.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56
            s = s.replace(',', '')
    elif ',' in s and not '.' in s:
        # Could be 1234,56 (EU) or 1,234 (US) — check position
        if len(s.split(',')[-1]) == 2:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    try:
        return float(Decimal(s))
    except (InvalidOperation, ValueError):
        return None


def _parse_date(s: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD."""
    if not s:
        return None
    s = s.strip()
    # Already ISO-ish
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s
    # Formats to try
    formats = [
        '%B %d, %Y',      # May 20, 2026
        '%b %d, %Y',      # May 20, 2026
        '%d %B %Y',       # 20 May 2026
        '%d %b %Y',       # 20 May 2026
        '%m/%d/%Y',       # 05/20/2026
        '%d/%m/%Y',       # 20/05/2026
        '%Y/%m/%d',       # 2026/05/20
        '%d-%m-%Y',       # 20-05-2026
        '%m-%d-%Y',       # 05-20-2026
        '%d.%m.%Y',       # 20.05.2026
        '%B %Y',          # May 2026 → use 1st
        '%b %Y',          # May 2026
        '%m/%Y',          # 05/2026
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    # Try with dateutil-style fuzzy
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', s)
    if match:
        a, b, c = match.groups()
        year = int(c) if len(c) == 4 else 2000 + int(c)
        try:
            # Assume m/d/y order
            return f'{year:04d}-{int(a):02d}-{int(b):02d}'
        except ValueError:
            pass
    return None


def _rule_extract(text: str) -> dict:
    """Extract invoice data using regex patterns. Good fallback without AI."""
    result = {
        "vendor_name": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "total_amount": None,
        "currency": _detect_currency(text),
        "tax_amount": None,
        "line_items": [],
    }

    lines = text.split('\n')

    # --- Vendor name: first non-empty line, capitalized ---
    for line in lines[:10]:
        stripped = line.strip()
        if stripped and not re.match(r'(?i)(invoice|date|bill|tax|address|phone|email|www|http|po\s|p\.?o\.)', stripped):
            # Skip if it looks like an address component
            if re.match(r'^\d+ ', stripped):
                continue
            result["vendor_name"] = stripped
            break

    # --- Invoice number ---
    for line in lines:
        m = re.search(r'(?i)invoice\s*(#|number|num|no)?[:.\s]*([A-Z0-9\-]{3,30})', line)
        if m:
            result["invoice_number"] = m.group(2).strip()
            break

    # --- Dates ---
    for line in lines:
        # Invoice date
        m_date = re.search(r'(?i)(?:invoice\s+)?date[:.\s]*([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{2,4}|\d{1,4}[/\-.]\d{1,2}[/\-.]\d{2,4})', line)
        if m_date and not result["invoice_date"]:
            result["invoice_date"] = _parse_date(m_date.group(1))
        # Due date (match "Due Date:", "Due:", "Payment Due:")
        m_due = re.search(r'(?i)(?:due|payment)\s*(?:date)?[:.\s]*([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{2,4}|\d{1,4}[/\-.]\d{1,2}[/\-.]\d{2,4})', line)
        if m_due and not result["due_date"]:
            result["due_date"] = _parse_date(m_due.group(1))

    # --- Total ---
    for i, line in enumerate(lines):
        if re.search(r'(?i)^\s*(total|amount\s+due|balance\s+due|grand\s+total|invoice\s+total)\s*[:.]?\s*', line):
            # Check if amount is on same line
            amounts = re.findall(r'[\$\€\£\¥]?\s*[\d,]+\.?\d{2}', line)
            if amounts:
                result["total_amount"] = _parse_amount(amounts[-1])
                break
            # Amount might be on next line (table layout)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                amt = _parse_amount(next_line)
                if amt:
                    result["total_amount"] = amt
                    break
    # Fallback: look for "TOTAL" in a line with a large number
    if not result["total_amount"]:
        candidates = []
        for i, line in enumerate(lines):
            if re.search(r'(?i)\btotal\b', line) and not re.search(r'(?i)sub\s*total', line):
                nums = re.findall(r'[\$\€\£\¥]?\s*[\d,]+\.?\d{2}', line)
                for n in nums:
                    val = _parse_amount(n)
                    if val:
                        candidates.append(val)
                # Check next line for amount
                if not nums and i + 1 < len(lines):
                    amt = _parse_amount(lines[i + 1])
                    if amt:
                        candidates.append(amt)
        if candidates:
            result["total_amount"] = max(candidates)

    # --- Tax ---
    for i, line in enumerate(lines):
        # Exclude "Tax ID", "Tax Number", "Taxpayer", "VAT Number", "VAT Reg"
        if re.search(r'(?i)\b(tax\s*id|tax\s*number|taxpayer|vat\s*(number|reg|registration|no|id))', line):
            continue
        if re.search(r'(?i)\b(tax|vat|gst|hst|sales\s+tax)\b', line):
            # Check current line for amount with currency symbol or decimal
            nums = re.findall(r'[\$\€\£\¥]\s*[\d,]+\.\d{2}', line)
            if nums:
                amt = _parse_amount(nums[-1])
                if amt and amt < 1_000_000:  # sanity: tax shouldn't be millions
                    result["tax_amount"] = amt
                    break
            # Check next line for amount (table layout)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Must look like money (currency symbol or .XX format)
                if re.match(r'^[\$\€\£\¥]?\s*[\d,]+\.\d{2}$', next_line):
                    amt = _parse_amount(next_line)
                    if amt and amt < 1_000_000:
                        result["tax_amount"] = amt
                        break

    # --- Line items ---
    # PDF table extraction: cells often appear as lines in order (col1, col2, col3, col4...)
    # Detect table header row (columns: description, qty, unit_price, amount)
    header_idx = -1
    col_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in ('description', 'item', 'product', 'service', 'desc'):
            # Look ahead to count how many consecutive header cells
            header_idx = i
            # Count how many consecutive lines look like headers
            j = i
            header_words = {'description','item','product','service','desc','qty','quantity','unit','rate','price','amount','total','tax','vat'}
            while j < len(lines) and j - i < 6:
                s = lines[j].strip().lower()
                # Single-word header match
                if s in header_words:
                    j += 1
                    continue
                # Multi-word header: check if all words are header keywords
                words = re.split(r'[\s/]+', s)
                if len(words) >= 2 and all(w in header_words for w in words):
                    j += 1
                    continue
                break
            col_count = j - i
            break

    if col_count >= 3:
        # Extract data rows: each row has col_count consecutive non-empty lines
        data_rows = []
        current_row = []
        row_start = header_idx + col_count

        for i in range(row_start, len(lines)):
            stripped = lines[i].strip()
            # Stop at subtotal/total markers
            if re.search(r'(?i)^\s*(sub\s*total|total|tax|vat|balance|grand)', stripped):
                break
            if stripped:
                current_row.append(stripped)
                if len(current_row) == col_count:
                    data_rows.append(current_row)
                    current_row = []
            elif current_row:
                # Empty line while collecting — flush partial row?
                pass

        # Parse each row by column position
        for row in data_rows:
            item = {}
            for ci, val in enumerate(row):
                header = lines[header_idx + ci].strip().lower()
                parsed = _parse_amount(val)

                if 'desc' in header or 'item' in header or 'product' in header or 'service' in header:
                    item['description'] = val
                elif 'qty' in header or 'quantity' in header:
                    item['quantity'] = int(parsed) if parsed and parsed == int(parsed) else (parsed or 1)
                elif 'unit' in header or 'rate' in header or 'price' in header:
                    item['unit_price'] = parsed
                elif 'amount' in header or 'total' in header or 'tax' in header or 'vat' in header:
                    item['amount'] = parsed

            if item.get('description') and item.get('amount'):
                result['line_items'].append(item)

    # Fallback: single-line parsing (comma/space-separated)
    if not result['line_items']:
        for line in lines:
            stripped = line.strip()
            parts = re.split(r'\s{2,}', stripped)
            if len(parts) >= 3:
                numeric_parts = []
                text_parts = []
                for p in parts:
                    cleaned = p.strip().replace('$', '').replace('€', '').replace(',', '')
                    try:
                        float(cleaned)
                        numeric_parts.append(p.strip())
                    except ValueError:
                        text_parts.append(p.strip())

                if len(numeric_parts) >= 2:
                    description = ' '.join(text_parts) if text_parts else parts[0]
                    amounts = [_parse_amount(n) for n in numeric_parts]
                    amounts = [a for a in amounts if a is not None]

                    if len(amounts) >= 2:
                        item = {"description": description, "amount": amounts[-1]}
                        remaining = sorted(amounts[:-1], reverse=True)
                        if len(remaining) >= 2:
                            item["unit_price"] = remaining[0]
                            item["quantity"] = remaining[1]
                        elif remaining:
                            if remaining[0] == int(remaining[0]) and remaining[0] < 1000:
                                item["quantity"] = int(remaining[0])
                                item["unit_price"] = round(item["amount"] / item["quantity"], 2) if item["amount"] else None
                            else:
                                item["unit_price"] = remaining[0]
                                item["quantity"] = round(item["amount"] / item["unit_price"], 4) if item["amount"] else None
                        result['line_items'].append(item)

    return result


# ============================================================================
# AI extraction
# ============================================================================

def _ai_extract(text: str) -> dict:
    """Send extracted text to AI model and return structured invoice data."""
    from openai import OpenAI

    client = OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
    )

    prompt = f"""You are an invoice data extractor. Extract structured data from the following invoice text.

Return ONLY valid JSON (no markdown, no code fences, no extra text) with this exact structure:
{{
  "vendor_name": "Company name on the invoice",
  "invoice_number": "INV-12345",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "total_amount": 123.45,
  "currency": "USD",
  "tax_amount": 12.34 or null,
  "line_items": [
    {{
      "description": "Item description",
      "quantity": 1,
      "unit_price": 100.00,
      "amount": 100.00
    }}
  ]
}}

Rules:
- Extract ALL visible line items from the invoice.
- For dates, always use YYYY-MM-DD format. If only month/year, use the 1st.
- Amounts should be numbers without currency symbols.
- If a field is not found, use null.
- If the text doesn't look like an invoice, still extract what you can.
- Be precise with numbers — don't hallucinate.

Invoice text:
{text[:6000]}
"""

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": "You are a precise invoice data extractor. Return only valid JSON, no explanation."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # Clean any potential markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"AI response is not valid JSON: {raw[:200]}")

    return data


def _merge_results(rule: dict, ai: dict) -> dict:
    """Merge AI and rule-based results. AI takes priority, rules fill gaps."""
    merged = {}
    for key in ["vendor_name", "invoice_number", "invoice_date", "due_date",
                 "total_amount", "currency", "tax_amount", "line_items"]:
        ai_val = ai.get(key)
        rule_val = rule.get(key)
        if ai_val is not None and ai_val != "" and ai_val != []:
            merged[key] = ai_val
        elif rule_val is not None and rule_val != "" and rule_val != []:
            merged[key] = rule_val
        else:
            merged[key] = None
    # Special: line items — prefer whichever has more
    ai_items = ai.get("line_items") or []
    rule_items = rule.get("line_items") or []
    merged["line_items"] = ai_items if len(ai_items) >= len(rule_items) else rule_items
    return merged


def extract_invoice_data(pdf_bytes: bytes, filename: str = "invoice.pdf") -> "ExtractionResult":
    """
    Full pipeline: PDF text → rule-based extraction → (optional) AI merge.
    """
    from main import ExtractionResult

    # Step 1: Extract text from PDF
    raw_text = _extract_text_from_pdf(pdf_bytes)

    if not raw_text.strip():
        raise ValueError(
            "Could not extract text from this PDF. "
            "It may be a scanned image or contain no selectable text."
        )

    # Step 2: Always run rule-based extraction
    rule_data = _rule_extract(raw_text)

    # Step 3: AI extraction (when available)
    ai_data = None
    if AI_API_KEY:
        try:
            ai_data = _ai_extract(raw_text)
        except Exception as e:
            # AI failed — use rules only
            pass

    # Step 4: Merge
    if ai_data:
        data = _merge_results(rule_data, ai_data)
    else:
        data = rule_data

    return ExtractionResult(
        vendor_name=data.get("vendor_name"),
        invoice_number=data.get("invoice_number"),
        invoice_date=data.get("invoice_date"),
        due_date=data.get("due_date"),
        total_amount=data.get("total_amount"),
        currency=data.get("currency", "USD"),
        tax_amount=data.get("tax_amount"),
        line_items=data.get("line_items", []),
        raw_text_preview=raw_text[:500],
    )
