import os
import re
import json
import sqlite3
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import database
import extractor

# --- FOLDERS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Priority 1: 'static' folder inside backend
STATIC_DIR = os.path.join(BASE_DIR, 'static')
# Priority 2: 'dist' folder in frontend
if not os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
    STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'dist'))

print(f"--- FinExtract Engine ---")
print(f"UI Source: {STATIC_DIR}")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/')
CORS(app)

database.init_db()

# Helper
def get_year_num(year_str):
    m = re.search(r'\d+', year_str)
    return int(m.group(0)) if m else 0

def process_growth_and_cagr(kpi_records):
    groups = {}
    for r in kpi_records:
        kpi = r['kpi_name']
        if kpi not in groups: groups[kpi] = []
        groups[kpi].append(r)
    all_processed = []
    for kpi, records in groups.items():
        sorted_records = sorted(records, key=lambda x: get_year_num(x['fiscal_year']))
        for i in range(len(sorted_records)):
            sorted_records[i]['yoy_growth'] = None
            if i > 0:
                prev, curr = sorted_records[i-1], sorted_records[i]
                if get_year_num(curr['fiscal_year']) - get_year_num(prev['fiscal_year']) == 1 and prev['kpi_value_numeric'] != 0:
                    sorted_records[i]['yoy_growth'] = round(((curr['kpi_value_numeric'] - prev['kpi_value_numeric']) / abs(prev['kpi_value_numeric'])) * 100, 2)
        cagr = None
        if len(sorted_records) >= 2:
            first, last = sorted_records[0], sorted_records[-1]
            n = get_year_num(last['fiscal_year']) - get_year_num(first['fiscal_year'])
            if n >= 1 and first['kpi_value_numeric'] > 0 and last['kpi_value_numeric'] > 0:
                cagr = round(((last['kpi_value_numeric'] / first['kpi_value_numeric']) ** (1/n) - 1) * 100, 2)
        for r in sorted_records:
            r['cagr'] = cagr
            all_processed.append(r)
    return all_processed

# API
@app.route('/api/documents', methods=['GET'])
def list_documents():
    return jsonify(database.get_documents())

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    filename = file.filename
    filepath = os.path.join(BASE_DIR, "uploads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    doc_id = database.add_document(filename, filepath)
    return jsonify({'document_id': doc_id, 'filename': filename})

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    database.delete_document(doc_id)
    return jsonify({'success': True})

@app.route('/api/extract', methods=['POST'])
def trigger_extraction():
    data = request.json
    doc_id, kpis = data['document_id'], data['kpis']
    custom = data.get('custom_kpis', [])
    doc = database.get_document(doc_id)
    database.clear_kpis_for_document(doc_id)
    results = extractor.run_extraction(doc['filepath'], kpis, custom)
    for r in results:
        database.save_extracted_kpi(doc_id, r['kpi_name'], r['kpi_value_raw'], r['kpi_value_numeric'],
                                   r['fiscal_year'], r['page_number'], r['source_text'], r['confidence'], r['is_custom'])
    return get_results(doc_id)

@app.route('/api/results/<int:doc_id>', methods=['GET'])
def get_results(doc_id):
    kpis = database.get_extracted_kpis(doc_id)
    return jsonify({'kpis': process_growth_and_cagr(kpis)})

# Dashboard Route
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all for SPA and static assets
@app.route('/<path:path>')
def static_proxy(path):
    # Try serving as a direct file from static folder
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise, fallback to index.html (SPA support)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
