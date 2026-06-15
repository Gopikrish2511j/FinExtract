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
    text = str(text).strip().upper()
    if len(text) > 30:
        return None
    
    # Patterns:
    # 2024-25 or 2024/25 -> FY25
    m = re.search(r'\b20(\d{2})[-/](\d{2})\b', text)
    if m:
        return f"FY{m.group(2)}"
    # FY 2025 or FY2025 -> FY25
    m = re.search(r'\bFY\s*20(\d{2})\b', text)
    if m:
        return f"FY{m.group(1)}"
    # FY 25 or FY25 -> FY25
    m = re.search(r'\bFY\s*(\d{2})\b', text)
    if m:
        return f"FY{m.group(1)}"
    # 2025 or 2024 -> FY25
    m = re.search(r'\b20(\d{2})\b', text)
    if m:
        return f"FY{m.group(1)}"
        
    return None

def parse_numeric_value(val_str):
    if not val_str:
        return None, None
        
    cleaned = val_str.strip()
    is_negative = False
    
    # Check if negative: e.g. (1,234.50) or -1,234.50 or –1,234.50
    if (cleaned.startswith('(') and cleaned.endswith(')')) or cleaned.startswith('-') or cleaned.startswith('–'):
        is_negative = True
        cleaned = cleaned.replace('(', '').replace(')', '').replace('-', '').replace('–', '').strip()
        
    # Remove currency symbols and non-essential characters
    cleaned = re.sub(r'[^\d\.\s,a-zA-Z]', '', cleaned)
    
    # Extract the number part: e.g. 9,150.50
    num_match = re.search(r'[\d,]+(?:\.\d+)?', cleaned)
    if not num_match:
        return None, None
        
    num_str = num_match.group(0)
    try:
        val_float = float(num_str.replace(',', '').strip())
    except ValueError:
        return None, None
        
    if is_negative:
        val_float = -val_float
        
    # Suffixes
    suffix = cleaned[num_match.end():].strip().lower()
    prefix = cleaned[:num_match.start()].strip().lower()
    combined_text = prefix + " " + suffix
    
    multiplier = 1.0
    
    if 'cr' in combined_text or 'crore' in combined_text:
        multiplier = 10000000.0 # Crore = 10 million
    elif 'bn' in combined_text or 'billion' in combined_text or re.search(r'\bb\b', combined_text):
        multiplier = 1000000000.0
    elif 'million' in combined_text or 'mn' in combined_text or re.search(r'\bm\b', combined_text):
        multiplier = 1000000.0
    elif 'lakh' in combined_text:
        multiplier = 100000.0
        
    normalized_value = val_float * multiplier
    return val_str, normalized_value

def find_matching_kpi(text, synonyms):
    text_lower = text.lower()
    for kpi, syn_list in synonyms.items():
        for syn in syn_list:
            pattern = r'\b' + re.escape(syn.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return kpi
    return None

def extract_from_tables(pdf_path, synonyms):
    extracted = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                tables = page.extract_tables()
                if not tables:
                    continue
                    
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Inspect first 3 rows to find headers representing years
                    header_row = None
                    year_cols = {}
                    
                    for r_idx in range(min(len(table), 3)):
                        row = table[r_idx]
                        if not row:
                            continue
                        for col_idx, cell in enumerate(row):
                            if cell:
                                norm_y = normalize_year(cell)
                                if norm_y:
                                    year_cols[col_idx] = norm_y
                                    header_row = r_idx
                                    
                    if not year_cols or header_row is None:
                        continue
                        
                    # Scan rows below header row
                    for r_idx in range(header_row + 1, len(table)):
                        row = table[r_idx]
                        if not row or len(row) < 2:
                            continue
                            
                        # Find row label in first or second column
                        row_label = ""
                        for c_idx in range(min(2, len(row))):
                            cell_content = row[c_idx]
                            if cell_content and not normalize_year(cell_content) and len(str(cell_content).strip()) > 2:
                                row_label = str(cell_content).strip()
                                break
                                
                        if not row_label:
                            continue
                            
                        matched_kpi = find_matching_kpi(row_label, synonyms)
                        if matched_kpi:
                            # Extract for matching year columns
                            for col_idx, year in year_cols.items():
                                if col_idx < len(row):
                                    cell_val = row[col_idx]
                                    if cell_val and cell_val.strip():
                                        raw_val, numeric_val = parse_numeric_value(cell_val)
                                        if numeric_val is not None:
                                            # Create a contextual source text snippet
                                            table_header_cells = [str(table[header_row][c]) for c in year_cols if c < len(row)]
                                            table_row_cells = [str(row[c]) for c in year_cols if c < len(row)]
                                            snippet = f"Table row: '{row_label}' | Columns: {table_header_cells} | Values: {table_row_cells}"
                                            
                                            extracted.append({
                                                'kpi_name': matched_kpi,
                                                'kpi_value_raw': raw_val,
                                                'kpi_value_numeric': numeric_val,
                                                'fiscal_year': year,
                                                'page_number': page_num,
                                                'source_text': snippet,
                                                'confidence': 95
                                            })
    except Exception as e:
        print(f"Error in table extraction: {e}")
        
    return extracted

def extract_from_text(pdf_path, synonyms):
    extracted = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                for line_idx, line in enumerate(lines):
                    matched_kpi = find_matching_kpi(line, synonyms)
                    if not matched_kpi:
                        continue
                        
                    # Find year in this line or 3 preceding lines
                    year_match = normalize_year(line)
                    if not year_match:
                        for offset in range(1, 4):
                            if line_idx - offset >= 0:
                                prev_line = lines[line_idx - offset]
                                year_match = normalize_year(prev_line)
                                if year_match:
                                    break
                                    
                    if not year_match:
                        continue
                        
                    # Find numbers
                    numbers = re.finditer(r'\b(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:Cr|Crore|Crores|Million|Mn|M|Billion|Bn|B|Lakh|Lakhs|L)?\b', line, re.IGNORECASE)
                    for num_match in numbers:
                        val_str = num_match.group(0)
                        # Exclude matches that look like the year itself
                        if val_str.strip() in year_match or "20" + val_str.strip() in year_match:
                            continue
                            
                        raw_val, numeric_val = parse_numeric_value(val_str)
                        if numeric_val is not None:
                            # Filter small unrelated integers
                            if abs(numeric_val) < 10 and '.' not in val_str and matched_kpi not in ["EPS", "Debt To Equity"]:
                                continue
                                
                            confidence = 80
                            snippet = line.strip()
                            if year_match not in line:
                                snippet = f"[Context: {year_match}] " + snippet
                                
                            extracted.append({
                                'kpi_name': matched_kpi,
                                'kpi_value_raw': raw_val,
                                'kpi_value_numeric': numeric_val,
                                'fiscal_year': year_match,
                                'page_number': page_num,
                                'source_text': snippet,
                                'confidence': confidence
                            })
                            break # Match first valid numeric value in line
    except Exception as e:
        print(f"Error in text extraction: {e}")
        
    return extracted

def run_extraction(pdf_path, target_kpis, custom_kpis=None):
    """
    Run table and text extraction for target_kpis + custom_kpis
    """
    predefined_syns = load_synonyms()
    
    # Construct target synonyms dictionary
    active_syns = {}
    
    # 1. Filter predefined synonyms for target KPIs
    for kpi in target_kpis:
        if kpi in predefined_syns:
            active_syns[kpi] = predefined_syns[kpi]
        else:
            # Fallback if KPI doesn't have predefined synonyms
            active_syns[kpi] = [kpi]
            
    # 2. Add custom KPIs
    if custom_kpis:
        for kpi in custom_kpis:
            kpi_clean = kpi.strip()
            if kpi_clean:
                # Add word boundary variations
                active_syns[kpi_clean] = [
                    kpi_clean,
                    kpi_clean.lower(),
                    kpi_clean + "s",
                    kpi_clean.lower() + "s",
                    kpi_clean.replace(" ", "")
                ]
                
    # Run both extractors
    table_results = extract_from_tables(pdf_path, active_syns)
    text_results = extract_from_text(pdf_path, active_syns)
    
    # Merge results (prefer tables for higher confidence)
    merged = {}
    
    for r in table_results + text_results:
        key = (r['kpi_name'], r['fiscal_year'])
        
        # Determine if this KPI is custom
        is_custom_flag = 1 if custom_kpis and r['kpi_name'] in custom_kpis else 0
        r['is_custom'] = is_custom_flag
        
        if key not in merged:
            merged[key] = r
        else:
            # Keep table results (higher confidence)
            if r['confidence'] > merged[key]['confidence']:
                merged[key] = r
                
    return list(merged.values())

if __name__ == "__main__":
    # Test stub
    import sys
    if len(sys.argv) > 1:
        pdf = sys.argv[1]
        print(f"Testing extraction on {pdf}...")
        results = run_extraction(pdf, ["Revenue", "PAT", "EBITDA"], ["Employee Cost"])
        for r in results:
            print(f"{r['kpi_name']} | {r['fiscal_year']} | {r['kpi_value_raw']} | Numeric: {r['kpi_value_numeric']} | Page: {r['page_number']} | Confidence: {r['confidence']}% (Custom: {r['is_custom']})")
    else:
        print("Provide a PDF path to run testing.")
