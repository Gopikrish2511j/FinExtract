import os
import re
import json
import pdfplumber

def load_synonyms():
    # Assets are in the same dir as the script in Chaquopy
    syn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synonyms.json")
    if os.path.exists(syn_path):
        with open(syn_path, "r") as f:
            return json.load(f)
    return {}

def normalize_year(text):
    text = str(text).strip().upper()
    if len(text) > 30: return None
    m = re.search(r'\b20(\d{2})[-/](\d{2})\b', text)
    if m: return f"FY{m.group(2)}"
    m = re.search(r'\bFY\s*20(\d{2})\b', text)
    if m: return f"FY{m.group(1)}"
    m = re.search(r'\bFY\s*(\d{2})\b', text)
    if m: return f"FY{m.group(1)}"
    m = re.search(r'\b20(\d{2})\b', text)
    if m: return f"FY{m.group(1)}"
    return None

def parse_numeric_value(val_str):
    if not val_str: return None, None
    cleaned = val_str.strip()
    is_negative = False
    if (cleaned.startswith('(') and cleaned.endswith(')')) or cleaned.startswith('-') or cleaned.startswith('–'):
        is_negative = True
        cleaned = cleaned.replace('(', '').replace(')', '').replace('-', '').replace('–', '').strip()
    cleaned = re.sub(r'[^\d\.\s,a-zA-Z]', '', cleaned)
    num_match = re.search(r'[\d,]+(?:\.\d+)?', cleaned)
    if not num_match: return None, None
    num_str = num_match.group(0)
    try:
        val_float = float(num_str.replace(',', '').strip())
    except ValueError: return None, None
    if is_negative: val_float = -val_float
    suffix = cleaned[num_match.end():].strip().lower()
    prefix = cleaned[:num_match.start()].strip().lower()
    combined_text = prefix + " " + suffix
    multiplier = 1.0
    if 'cr' in combined_text or 'crore' in combined_text: multiplier = 10000000.0
    elif 'bn' in combined_text or 'billion' in combined_text or re.search(r'\bb\b', combined_text): multiplier = 1000000000.0
    elif 'million' in combined_text or 'mn' in combined_text or re.search(r'\bm\b', combined_text): multiplier = 1000000.0
    elif 'lakh' in combined_text: multiplier = 100000.0
    return val_str, val_float * multiplier

def find_matching_kpi(text, synonyms):
    text_lower = text.lower()
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
                    year_cols = {}
                    header_row = None
                    for r_idx in range(min(len(table), 3)):
                        for col_idx, cell in enumerate(table[r_idx]):
                            if cell:
                                norm_y = normalize_year(cell)
                                if norm_y:
                                    year_cols[col_idx] = norm_y
                                    header_row = r_idx
                    if not year_cols or header_row is None: continue
                    for r_idx in range(header_row + 1, len(table)):
                        row = table[r_idx]
                        row_label = ""
                        for c_idx in range(min(2, len(row))):
                            if row[c_idx] and not normalize_year(row[c_idx]) and len(str(row[c_idx]).strip()) > 2:
                                row_label = str(row[c_idx]).strip()
                                break
                        if not row_label: continue
                        matched_kpi = find_matching_kpi(row_label, synonyms)
                        if matched_kpi:
                            for col_idx, year in year_cols.items():
                                if col_idx < len(row) and row[col_idx]:
                                    raw_val, num_val = parse_numeric_value(row[col_idx])
                                    if num_val is not None:
                                        extracted.append({
                                            'kpi_name': matched_kpi, 'kpi_value_raw': raw_val, 'kpi_value_numeric': num_val,
                                            'fiscal_year': year, 'page_number': page_idx+1,
                                            'source_text': f"Table: {row_label}", 'confidence': 95
                                        })
    except: pass
    return extracted

def run_extraction(pdf_path, target_kpis, custom_kpis=None):
    syns = load_synonyms()
    active_syns = {k: syns.get(k, [k]) for k in target_kpis}
    if custom_kpis:
        for k in custom_kpis:
            if k.strip(): active_syns[k.strip()] = [k.strip(), k.strip().lower()]

    # Text extraction simplified for performance on mobile
    results = extract_from_tables(pdf_path, active_syns)
    merged = {}
    for r in results:
        key = (r['kpi_name'], r['fiscal_year'])
        r['is_custom'] = 1 if custom_kpis and r['kpi_name'] in custom_kpis else 0
        if key not in merged or r['confidence'] > merged[key]['confidence']:
            merged[key] = r
    return list(merged.values())
