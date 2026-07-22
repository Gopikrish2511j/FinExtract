import os
import re
import json
import pdfplumber

def load_synonyms():
    syn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synonyms.json")
    if os.path.exists(syn_path):
        with open(syn_path, "r") as f:
            return json.load(f)
    return {}

def normalize_year(text):
    if not text: return None
    text = str(text).strip().upper().replace("\n", " ")
    if len(text) > 40: return None

    # 2024-25 -> FY25
    m = re.search(r'\b20(\d{2})[-/](\d{2})\b', text)
    if m: return f"FY{m.group(2)}"
    # FY 2025 -> FY25
    m = re.search(r'\bFY\s*20(\d{2})\b', text)
    if m: return f"FY{m.group(1)}"
    # FY 25 -> FY25
    m = re.search(r'\bFY\s*(\d{2})\b', text)
    if m: return f"FY{m.group(1)}"
    # 2025 -> FY25
    m = re.search(r'\b(20\d{2})\b', text)
    if m: return f"FY{m.group(1)[2:]}"
    return None

def parse_numeric_value(val_str):
    if not val_str: return None, None
    cleaned = str(val_str).strip().replace("\n", " ")
    is_negative = False
    if (cleaned.startswith('(') and cleaned.endswith(')')) or cleaned.startswith('-') or cleaned.startswith('–'):
        is_negative = True
        cleaned = cleaned.replace('(', '').replace(')', '').replace('-', '').replace('–', '').strip()

    cleaned = re.sub(r'[^\d\.\s,a-zA-Z]', '', cleaned)
    num_match = re.search(r'[\d,]+(?:\.\d+)?', cleaned)
    if not num_match: return None, None

    num_str = num_match.group(0).replace(',', '')
    try:
        val_float = float(num_str)
    except ValueError: return None, None

    if is_negative: val_float = -val_float

    combined_text = cleaned.lower()
    multiplier = 1.0
    if 'cr' in combined_text or 'crore' in combined_text: multiplier = 10000000.0
    elif 'bn' in combined_text or 'billion' in combined_text or re.search(r'\bb\b', combined_text): multiplier = 1000000000.0
    elif 'million' in combined_text or 'mn' in combined_text or re.search(r'\bm\b', combined_text): multiplier = 1000000.0
    elif 'lakh' in combined_text: multiplier = 100000.0

    return val_str, val_float * multiplier

def find_matching_kpi(text, synonyms):
    if not text: return None
    text_lower = text.lower().replace("\n", " ")
    for kpi, syn_list in synonyms.items():
        for syn in syn_list:
            if re.search(r'\b' + re.escape(syn.lower()) + r'\b', text_lower):
                return kpi
    return None

def extract_from_tables(pdf_path, synonyms):
    extracted = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if not tables: continue
                for table in tables:
                    if not table or len(table) < 2: continue

                    # 1. Advanced Header Recovery
                    # Sometimes headers are split across multiple rows
                    year_cols = {}
                    header_rows_count = 0
                    for r_idx in range(min(len(table), 4)):
                        found_year = False
                        for col_idx, cell in enumerate(table[r_idx]):
                            norm_y = normalize_year(cell)
                            if norm_y:
                                year_cols[col_idx] = norm_y
                                found_year = True
                        if found_year: header_rows_count = r_idx + 1

                    if not year_cols: continue

                    # 2. Row Processing with Label Merging
                    prev_label = ""
                    for r_idx in range(header_rows_count, len(table)):
                        row = table[r_idx]
                        if not row: continue

                        # Get label from first few columns
                        current_label_parts = [str(c).strip() for c in row[:2] if c and not normalize_year(c)]
                        current_label = " ".join(current_label_parts)

                        # Handle split rows (where label is on one row and values on next, or vice versa)
                        if not current_label and prev_label:
                            full_label = prev_label
                        elif current_label and len(current_label) < 4 and prev_label:
                            full_label = f"{prev_label} {current_label}"
                        else:
                            full_label = current_label

                        matched_kpi = find_matching_kpi(full_label, synonyms)
                        if matched_kpi:
                            for col_idx, year in year_cols.items():
                                if col_idx < len(row) and row[col_idx]:
                                    raw, num = parse_numeric_value(row[col_idx])
                                    if num is not None:
                                        extracted.append({
                                            'kpi_name': matched_kpi, 'kpi_value_raw': raw, 'kpi_value_numeric': num,
                                            'fiscal_year': year, 'page_number': page_idx+1,
                                            'source_text': f"Table: {full_label}", 'confidence': 98
                                        })
                        prev_label = full_label
    except Exception as e: print(f"Table Error: {e}")
    return extracted

def extract_from_text(pdf_path, synonyms):
    extracted = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text: continue
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    kpi = find_matching_kpi(line, synonyms)
                    if not kpi: continue

                    # Find year in current or nearby lines
                    year = None
                    for offset in range(-2, 3):
                        if 0 <= i + offset < len(lines):
                            year = normalize_year(lines[i + offset])
                            if year: break
                    if not year: continue

                    # Find number in line
                    numbers = re.finditer(r'\b(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:Cr|Crore|Million|Mn|Bn|Lakh)?\b', line, re.IGNORECASE)
                    for match in numbers:
                        raw, num = parse_numeric_value(match.group(0))
                        if num is not None:
                            extracted.append({
                                'kpi_name': kpi, 'kpi_value_raw': raw, 'kpi_value_numeric': num,
                                'fiscal_year': year, 'page_number': page_idx+1,
                                'source_text': line.strip(), 'confidence': 85
                            })
                            break
    except: pass
    return extracted

def run_extraction(pdf_path, target_kpis, custom_kpis=None):
    syns = load_synonyms()
    active_syns = {k: syns.get(k, [k]) for k in target_kpis}
    if custom_kpis:
        for k in custom_kpis:
            if k.strip(): active_syns[k.strip()] = [k.strip(), k.strip().lower()]

    results = extract_from_tables(pdf_path, active_syns) + extract_from_text(pdf_path, active_syns)
    merged = {}
    for r in results:
        key = (r['kpi_name'], r['fiscal_year'])
        r['is_custom'] = 1 if custom_kpis and r['kpi_name'] in custom_kpis else 0
        if key not in merged or r['confidence'] > merged[key]['confidence']:
            merged[key] = r
    return list(merged.values())
