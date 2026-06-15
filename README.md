# FinExtract – Financial Intelligence Platform

FinExtract is a high-performance, developer-focused, offline-first financial intelligence platform. It extracts core financial Key Performance Indicators (KPIs) from corporate annual reports (PDFs), normalizes data points, compares trends over multiple fiscal years (YoY & CAGR), renders visualizations, and exports styled Excel sheets.

---

## 🌟 Key Features

1. **Rule-Based Hybrid PDF Extractor**: Combines structured table parsing (accurate columns & rows map) with line-by-line regex keyword scanning to extract KPIs, source page references, and context.
2. **Dynamic KPI Checklist & Custom KPIs**: Users select from 16 default KPIs or input a custom KPI (e.g. "Employee Cost") to search the document text instantly.
3. **Investor-Focused Dashboard**: Beautiful dark theme dashboard featuring interactive trends line-charts and area-charts using Recharts.
4. **Source Traceability Details**: High auditing accuracy — click any cell in the results table to view the source page number and highlight the exact text snippet.
5. **YoY & CAGR Analytics Engine**: Computes Year-over-Year Growth percentages and Compounded Annual Growth Rates automatically.
6. **Polished Excel Exporting**: Generates multi-sheet styled worksheets with layout borders, alignment, and auto-adjusted width.
7. **PWA (Progressive Web App)**: Installable on Android devices with splash screens, icons, and offline support.
8. **Electron Shell**: Runs as a local Windows desktop application wrapper.

---

## 📂 Project Structure

```
/
├── backend/
│   ├── app.py                  # Flask server entrypoint (CORS & Excel endpoints)
│   ├── database.py             # SQLite DB utility (Documents & KPI tables)
│   ├── extractor.py            # pdfplumber parsing, numeric normalization & confidence scoring
│   ├── synonyms.json           # Configurable synonym mapping dictionary
│   ├── requirements.txt        # Python backend dependencies
│   ├── create_demo_pdf.py      # Script to generate a multi-year testing PDF
│   └── sample_annual_report.pdf # Generated PDF with sample numbers (9150 Cr, 1916 Cr, etc.)
├── frontend/
│   ├── index.html              # Vite entry page
│   ├── package.json            # React, Vite, TS, Recharts, Tailwind dependencies
│   ├── tailwind.config.js      # Tailwind configurations & theme design tokens
│   ├── src/
│   │   ├── main.tsx            # Main App mounting & PWA registration
│   │   ├── App.tsx             # Interactive dashboard logic & Recharts layout
│   │   ├── types.ts            # Common TS interfaces for KPI & Doc shapes
│   │   └── index.css           # Global stylesheet containing custom scrollbars & panels
│   └── public/
│       ├── manifest.json       # PWA web manifest file
│       ├── sw.js               # Service Worker caching script
│       ├── icon-192.png        # Icon file for mobile installation (192px)
│       └── icon-512.png        # Icon file for mobile installation (512px)
└── electron/
    ├── main.js                 # Electron main window & IPC initializer
    └── package.json            # Electron devDependencies & package commands
```

---

## 🚀 Setup & Launch Instructions (Live Demo)

### 1. Start the Flask Backend Server
Navigate to the root directory and set up the Python environment:
```powershell
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run the server (default port: 5000)
python backend/app.py
```
*Note: A SQLite database `backend/finextract.db` and the uploads folder `backend/uploads/` will be initialized automatically on startup.*

### 2. Generate the Sample Report (Optional)
If you want to test with a clean file containing multi-year financial statements matching the prompt:
```powershell
python backend/create_demo_pdf.py
```
This generates `backend/sample_annual_report.pdf` which you can upload directly in the dashboard.

### 3. Launch the Vite Frontend Dev Server
In a new terminal window:
```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Launch dev environment (default port: 5173)
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser. The connection indicator will turn green showing **"Local Engine Connected"**.

---

## 💻 Windows Desktop Application (Electron)

To wrap the web interface into a native Windows `.exe` application:

### 1. Launch in Dev Mode
Make sure your Vite server is running (`npm run dev` in `frontend/`), then:
```powershell
# 1. Navigate to electron directory
cd electron

# 2. Install Electron wrapper dependencies
npm install

# 3. Start the Electron window
npm start
```
This launches a custom desktop frame loading the dashboard.

### 2. Build the Windows Executable (`.exe`)
To package a standalone executable:
```powershell
# In the /electron folder, run:
npm run package
```
This executes `electron-builder` to package the static assets into a standalone distribution inside the `electron/dist/` folder.

---

## 📱 Android Mobile Installation (Progressive Web App)

FinExtract contains full PWA integration (web manifest, service worker caching, and prompt handler):

### 1. Install instructions
1. Host the project over HTTPS or access it in your mobile browser via local network sharing: `http://<your-local-ip>:5173`.
2. When opened in a mobile browser (Chrome/Edge on Android), a prompt button **"Install App (PWA)"** will appear on the top header.
3. Click the button or select **"Add to Home screen"** from the browser menu.
4. The application will install as a native shell with the custom icon and launch without standard browser address bars.

---

## 🏛️ Clean Architecture Explanation

FinExtract is structured around strict separation of concerns to maximize modularity and performance:

1. **Storage Layer (`backend/database.py`)**: Accesses data deterministically through SQLite. Contains isolated interfaces for adding/deleting documents and fetching/saving structured KPI logs.
2. **Extraction Engine (`backend/extractor.py`)**: Uses standard inputs and yields structured dictionary responses. It operates entirely offline without depending on cloud or API model services. Mappings are fed via a configurable `synonyms.json` file.
3. **Core API (`backend/app.py`)**: Houses routes for uploads, processing requests, and Excel builders using `openpyxl` to separate business logic from processing scripts.
4. **View Interface (`frontend/src/App.tsx`)**: Decouples presentation from API communication. State handlers manage active layouts, toggled KPI configurations, and Recharts graphs on the fly.
