import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Upload, Plus, Trash2, RefreshCw, CheckSquare, Square, 
  Search, ArrowUpDown, FileSpreadsheet, TrendingUp, 
  Info, BarChart3, Activity, HelpCircle, Download,
  Layers, Sparkles, Smartphone
} from 'lucide-react';
import { Capacitor, registerPlugin } from '@capacitor/core';
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import type { Document, ExtractedKPI } from './types';

interface PythonBridgePlugin {
  listDocuments(): Promise<{ json: string }>;
  uploadDocument(options: { name: string; data: string }): Promise<{ id: number }>;
  deleteDocument(options: { id: number }): Promise<void>;
  runExtraction(options: { id: number; kpis: string; custom: string }): Promise<{ json: string }>;
  getResults(options: { id: number }): Promise<{ json: string }>;
  exportExcel(options: { id: number }): Promise<{ data: string }>;
}

const PythonBridge = registerPlugin<PythonBridgePlugin>('PythonBridge');
const isNative = Capacitor.getPlatform() !== 'web';

const DEFAULT_KPIS = [
  "Revenue", "Net Sales", "EBITDA", "EBIT", "PAT", "Net Profit", 
  "EPS", "Operating Margin", "Gross Profit", "Operating Profit", 
  "Cash Flow", "Total Assets", "Total Liabilities", "Debt To Equity", 
  "Inventory", "Working Capital"
];

const API_BASE = "/api";

export default function App() {
  // Landing state
  const [showLanding, setShowLanding] = useState(true);

  // Documents state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeDoc, setActiveDoc] = useState<Document | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // KPI Selection state
  const [selectedKPIs, setSelectedKPIs] = useState<string[]>(["Revenue", "EBITDA", "PAT", "EPS"]);
  const [kpiSearch, setKpiSearch] = useState("");
  const [customKPIInput, setCustomKPIInput] = useState("");
  const [customKPIs, setCustomKPIs] = useState<string[]>([]);
  
  // Results state
  const [results, setResults] = useState<ExtractedKPI[]>([]);
  const [sortField, setSortField] = useState<keyof ExtractedKPI>('kpi_name');
  const [sortAsc, setSortAsc] = useState(true);
  const [tableSearch, setTableSearch] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState<string>("all");
  
  // Selected KPI trace detail state
  const [selectedTrace, setSelectedTrace] = useState<ExtractedKPI | null>(null);
  
  // Active chart KPI selection
  const [activeChartKpi, setActiveChartKpi] = useState<string>("Revenue");
  
  // Service status
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  
  // PWA state
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstallBtn, setShowInstallBtn] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check backend connection and load docs
  useEffect(() => {
    const checkConnection = async (isFresh = false) => {
      // If it's a fresh start (on mount), clear UI state
      if (isFresh) {
        setActiveDoc(null);
        setResults([]);
        setSelectedTrace(null);
      }

      if (isNative) {
        try {
          const { json } = await PythonBridge.listDocuments();
          const docs = JSON.parse(json);
          setDocuments(docs);
          setBackendConnected(true);
          // Only auto-select if we aren't forcing a fresh start
          if (!isFresh && docs.length > 0 && !activeDoc) {
            setActiveDoc(docs[0]);
          }
        } catch (e) {
          console.error("Native connection error", e);
          setBackendConnected(false);
        }
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/documents`);
        if (res.ok) {
          setBackendConnected(true);
          const docs = await res.json();
          setDocuments(docs);
          if (!isFresh && docs.length > 0 && !activeDoc) {
            setActiveDoc(docs[0]);
          }
        } else {
          setBackendConnected(false);
        }
      } catch (e) {
        setBackendConnected(false);
      }
    };
    
    // Initial Fresh Load
    checkConnection(true);

    // Landing screen timer
    const landingTimer = setTimeout(() => setShowLanding(false), 3000);

    // Refresh when the app comes back from background
    const handleResume = () => {
      console.log("App resumed, refreshing data...");
      checkConnection(false); // Just refresh, don't clear selection on resume
    };
    document.addEventListener('resume', handleResume);

    // Poll documents status occasionally
    const interval = setInterval(() => checkConnection(false), 10000);
    return () => {
      clearInterval(interval);
      clearTimeout(landingTimer);
      document.removeEventListener('resume', handleResume);
    };
  }, []);

  // Fetch results when active document changes
  useEffect(() => {
    if (activeDoc) {
      fetchResults(activeDoc.id);
      setSelectedTrace(null);
    } else {
      setResults([]);
      setSelectedTrace(null);
    }
  }, [activeDoc]);

  // BeforeInstallPrompt PWA Handler
  useEffect(() => {
    const handler = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallBtn(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstallPWA = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
      setShowInstallBtn(false);
    }
  };

  const fetchResults = async (docId: number) => {
    if (isNative) {
      try {
        const { json } = await PythonBridge.getResults({ id: docId });
        const data = JSON.parse(json);
        setResults(data);
        const available = Array.from(new Set(data.map((k: any) => k.kpi_name)));
        if (available.length > 0 && !available.includes(activeChartKpi)) {
          setActiveChartKpi(available[0] as string);
        }
      } catch (e) {
        console.error("Error fetching results", e);
      }
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/results/${docId}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.kpis);
        // Default chart KPI to the first available KPI if active KPI is not in results
        const available = Array.from(new Set(data.kpis.map((k: any) => k.kpi_name)));
        if (available.length > 0 && !available.includes(activeChartKpi)) {
          setActiveChartKpi(available[0] as string);
        }
      }
    } catch (e) {
      console.error("Error fetching results", e);
    }
  };

  // Upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError("Only PDF annual reports are supported.");
      return;
    }
    
    setIsUploading(true);
    setUploadError(null);
    
    if (isNative) {
      try {
        const reader = new FileReader();
        reader.onload = async () => {
          const base64 = (reader.result as string).split(',')[1];
          try {
            const { id } = await PythonBridge.uploadDocument({
              name: file.name,
              data: base64
            });
            const newDoc: Document = {
              id: id,
              filename: file.name,
              filepath: '',
              uploaded_at: new Date().toISOString()
            };
            setDocuments(prev => [newDoc, ...prev]);
            setActiveDoc(newDoc);
            triggerExtraction(id);
          } catch (err: any) {
            setUploadError(err.message || "Upload failed");
          } finally {
            setIsUploading(false);
          }
        };
        reader.readAsDataURL(file);
        return;
      } catch (err) {
        setUploadError("Error processing file on device.");
        setIsUploading(false);
        return;
      }
    }

    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        const newDoc: Document = {
          id: data.document_id,
          filename: data.filename,
          filepath: '',
          uploaded_at: new Date().toISOString()
        };
        setDocuments(prev => [newDoc, ...prev]);
        setActiveDoc(newDoc);
        // Automatically trigger extraction on upload
        triggerExtraction(data.document_id);
      } else {
        const errorData = await response.json();
        setUploadError(errorData.error || "Upload failed");
      }
    } catch (err) {
      setUploadError("Network connection error during upload.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Trigger Extraction
  const triggerExtraction = async (docId: number) => {
    setIsExtracting(true);
    if (isNative) {
      try {
        const { json } = await PythonBridge.runExtraction({
          id: docId,
          kpis: JSON.stringify(selectedKPIs),
          custom: JSON.stringify(customKPIs)
        });
        setResults(JSON.parse(json));
      } catch (e) {
        console.error("Extraction error", e);
      } finally {
        setIsExtracting(false);
      }
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: docId,
          kpis: selectedKPIs,
          custom_kpis: customKPIs
        })
      });
      if (response.ok) {
        const data = await response.json();
        setResults(data.kpis);
      }
    } catch (e) {
      console.error("Extraction error", e);
    } finally {
      setIsExtracting(false);
    }
  };

  // Delete Document
  const handleDeleteDoc = async (docId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this document? All extraction results will be lost.")) return;

    if (isNative) {
      try {
        await PythonBridge.deleteDocument({ id: docId });
        const updated = documents.filter(d => d.id !== docId);
        setDocuments(updated);
        if (activeDoc?.id === docId) {
          setActiveDoc(updated.length > 0 ? updated[0] : null);
        }
      } catch (e) {
        console.error(e);
      }
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/documents/${docId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        const updated = documents.filter(d => d.id !== docId);
        setDocuments(updated);
        if (activeDoc?.id === docId) {
          setActiveDoc(updated.length > 0 ? updated[0] : null);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Add Custom KPI
  const handleAddCustomKPI = (e: React.FormEvent) => {
    e.preventDefault();
    const kpi = customKPIInput.trim();
    if (!kpi) return;
    
    const updatedCustom = [...customKPIs, kpi];
    const updatedSelected = [...selectedKPIs, kpi];

    // Add to custom list if not already present
    if (!customKPIs.includes(kpi) && !DEFAULT_KPIS.includes(kpi)) {
      setCustomKPIs(updatedCustom);
      setSelectedKPIs(updatedSelected);
    }
    setCustomKPIInput("");
    
    // Trigger immediate reprocessing if we have an active document
    if (activeDoc) {
      setIsExtracting(true);
      if (isNative) {
        PythonBridge.runExtraction({
          id: activeDoc.id,
          kpis: JSON.stringify(updatedSelected),
          custom: JSON.stringify(updatedCustom)
        }).then(({ json }) => {
          setResults(JSON.parse(json));
          setActiveChartKpi(kpi);
        }).catch(err => console.error(err))
          .finally(() => setIsExtracting(false));
      } else {
        fetch(`${API_BASE}/extract`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_id: activeDoc.id,
            kpis: updatedSelected,
            custom_kpis: updatedCustom
          })
        }).then(res => res.json()).then(data => {
          setResults(data.kpis);
          setActiveChartKpi(kpi);
        }).catch(err => console.error(err))
          .finally(() => setIsExtracting(false));
      }
    }
  };

  // Toggle KPI checkbox
  const toggleKPI = (kpi: string) => {
    setSelectedKPIs(prev => 
      prev.includes(kpi) ? prev.filter(k => k !== kpi) : [...prev, kpi]
    );
  };

  // Export to Excel
  const handleExportExcel = async () => {
    if (!activeDoc) return;
    console.log("Exporting excel, isNative:", isNative);

    if (isNative) {
      try {
        console.log("Calling PythonBridge.exportExcel for doc:", activeDoc.id);
        const { data } = await PythonBridge.exportExcel({ id: activeDoc.id });
        console.log("Excel data received, length:", data.length);
        const blob = await fetch(`data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${data}`).then(res => res.blob());
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `FinExtract_${activeDoc.filename.replace('.pdf', '')}_Report.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } catch (e) {
        console.error("Native export error:", e);
      }
      return;
    }

    try {
      console.log("Calling web export API");
      const response = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: activeDoc.id
        })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `FinExtract_${activeDoc.filename.replace('.pdf', '')}_Report.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error("Export error", e);
    }
  };

  // Prepare Chart Data
  // Group results by Year for multi-series charts
  const prepareChartData = () => {
    const yearsMap: { [year: string]: any } = {};
    results.forEach(r => {
      const yr = r.fiscal_year;
      if (!yearsMap[yr]) {
        yearsMap[yr] = { name: yr };
      }
      // Store numeric coefficient for plotting
      yearsMap[yr][r.kpi_name] = r.kpi_value_numeric;
    });
    
    // Sort years chronologically, e.g. FY23, FY24, FY25
    return Object.values(yearsMap).sort((a: any, b: any) => {
      const numA = parseInt(a.name.replace(/\D/g, '')) || 0;
      const numB = parseInt(b.name.replace(/\D/g, '')) || 0;
      return numA - numB;
    });
  };

  const chartData = prepareChartData();
  const availableKPIsForCharts = Array.from(new Set(results.map(r => r.kpi_name)));

  // Sorting results handler
  const handleSort = (field: keyof ExtractedKPI) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  // Apply sorting, searching, and filtering
  const filteredResults = results
    .filter(r => {
      const matchSearch = r.kpi_name.toLowerCase().includes(tableSearch.toLowerCase()) || 
                          r.fiscal_year.toLowerCase().includes(tableSearch.toLowerCase()) ||
                          r.kpi_value_raw.toLowerCase().includes(tableSearch.toLowerCase());
      
      let matchConfidence = true;
      if (confidenceFilter === 'high') matchConfidence = r.confidence >= 90;
      else if (confidenceFilter === 'medium') matchConfidence = r.confidence >= 75 && r.confidence < 90;
      else if (confidenceFilter === 'low') matchConfidence = r.confidence < 75;
      
      return matchSearch && matchConfidence;
    })
    .sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      
      if (valA === null || valA === undefined) return sortAsc ? 1 : -1;
      if (valB === null || valB === undefined) return sortAsc ? -1 : 1;
      
      if (typeof valA === 'string') {
        return sortAsc 
          ? valA.localeCompare(valB as string) 
          : (valB as string).localeCompare(valA);
      } else {
        return sortAsc 
          ? (valA as number) - (valB as number) 
          : (valB as number) - (valA as number);
      }
    });

  // Unique KPIs for YoY comparison rendering
  const comparisonKPIs = Array.from(new Set(results.map(r => r.kpi_name)));

  // Helper to get color classes for confidence levels
  const getConfidenceBadge = (score: number) => {
    if (score >= 90) return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    if (score >= 75) return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Landing Overlay */}
      {showLanding && (
        <div className="landing-overlay landing-fade-out">
          <div className="animate-slide-down flex flex-col items-center">
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-white font-sans">
              FIN <span className="text-emerald-500">EXTRACT</span>
            </h1>
            <div className="h-1 w-24 bg-gradient-to-r from-emerald-500 to-blue-600 rounded-full mt-2" />
          </div>
          <div className="animate-slide-up mt-8">
            <div className="p-4 rounded-2xl bg-gradient-to-tr from-emerald-500 to-blue-600 shadow-2xl shadow-emerald-500/20">
              <Layers className="h-12 w-12 md:h-16 md:w-12 text-white" />
            </div>
          </div>
        </div>
      )}

      {/* Header Dashboard Nav */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-dark-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-gradient-to-tr from-emerald-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/10">
            <Layers className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-sans">FinExtract</h1>
              <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">MVP</span>
            </div>
            <p className="text-xs text-slate-400">AI-Powered Financial Intelligence Platform</p>
          </div>
        </div>

        {/* Backend Connectivity Status & PWA Install Button */}
        <div className="flex items-center gap-4">
          {backendConnected === true ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-xs text-emerald-400">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 pulse-border" />
              {isNative ? 'On-Device Engine Active' : 'Local Engine Connected'}
            </div>
          ) : backendConnected === false ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/25 text-xs text-rose-400">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
              {isNative ? 'Internal Engine Error' : 'Engine Offline (Check Flask)'}
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-400">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              Connecting...
            </div>
          )}

          {showInstallBtn && (
            <button 
              onClick={handleInstallPWA}
              className="glow-btn-emerald !py-1.5 text-xs h-9"
            >
              <Smartphone className="h-3.5 w-3.5" />
              Install App (PWA)
            </button>
          )}
        </div>
      </header>

      {/* Main Dashboard Layout Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-[1600px] w-full mx-auto">
        
        {/* Left Column: PDF Upload and KPI Selection (1/4 Column width) */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          
          {/* Module 1: Upload Panel */}
          <div className="glass-card p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
              <Upload className="h-4 w-4 text-emerald-400" /> 
              Upload & Documents
            </h2>
            
            {/* File Drag and Drop */}
            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-colors duration-200 ${
                isUploading 
                  ? 'border-emerald-500 bg-emerald-500/5' 
                  : 'border-slate-800 hover:border-slate-700 bg-dark-950/40 hover:bg-dark-950/70'
              }`}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                className="hidden" 
                accept=".pdf" 
              />
              <Upload className="mx-auto h-8 w-8 text-slate-500 mb-3" />
              <p className="text-sm font-medium text-slate-200">Drag annual report PDF here</p>
              <p className="text-xs text-slate-500 mt-1">or click to browse from device</p>
            </div>
            {uploadError && <p className="text-xs text-rose-400 mt-2 bg-rose-500/10 p-2 rounded border border-rose-500/20">{uploadError}</p>}
            
            {/* Recent Uploaded Docs List */}
            <div className="mt-5">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Recent Reports</h3>
              <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1">
                {documents.length === 0 ? (
                  <p className="text-xs text-slate-500 italic py-2 text-center">No reports uploaded yet.</p>
                ) : (
                  documents.map(doc => (
                    <div 
                      key={doc.id}
                      onClick={() => setActiveDoc(doc)}
                      className={`flex items-center justify-between p-2.5 rounded-lg border text-left cursor-pointer transition-all duration-200 ${
                        activeDoc?.id === doc.id
                          ? 'bg-slate-800/80 border-slate-700 text-white'
                          : 'bg-dark-950/40 border-slate-900 text-slate-400 hover:bg-slate-900/30'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <FileText className={`h-4 w-4 flex-shrink-0 ${activeDoc?.id === doc.id ? 'text-emerald-400' : 'text-slate-500'}`} />
                        <span className="text-xs font-medium truncate block">{doc.filename}</span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteDoc(doc.id, e)}
                        className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900/50"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Module 2: KPI Checklist Selection Panel */}
          <div className="glass-card p-5 flex-1 flex flex-col min-h-[380px]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <CheckSquare className="h-4 w-4 text-emerald-400" />
                KPI Selection
              </h2>
              <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-medium">
                {selectedKPIs.length} Selected
              </span>
            </div>

            {/* Custom KPI Creation Form */}
            <form onSubmit={handleAddCustomKPI} className="flex gap-1.5 mb-4">
              <input 
                type="text"
                placeholder="Enter custom KPI (e.g. Employee Cost)"
                value={customKPIInput}
                onChange={e => setCustomKPIInput(e.target.value)}
                className="flex-1 bg-dark-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-slate-700"
              />
              <button 
                type="submit"
                className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded px-2.5 text-white active:scale-95 transition-all duration-150"
              >
                <Plus className="h-4 w-4" />
              </button>
            </form>

            {/* KPI Search Box */}
            <div className="relative mb-3">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input 
                type="text"
                placeholder="Search predefined KPIs..."
                value={kpiSearch}
                onChange={e => setKpiSearch(e.target.value)}
                className="w-full bg-dark-950/60 border border-slate-800/80 rounded pl-8 pr-3 py-2 text-xs text-white focus:outline-none"
              />
            </div>

            {/* Checklist Loop */}
            <div className="flex-1 overflow-y-auto max-h-[350px] pr-1 flex flex-col gap-1.5">
              {/* Custom KPIs List */}
              {customKPIs.length > 0 && (
                <div className="mb-2">
                  <span className="text-[10px] uppercase font-semibold text-purple-400 tracking-wider block mb-1">Custom KPIs</span>
                  {customKPIs.map(kpi => (
                    <button 
                      key={kpi}
                      onClick={() => toggleKPI(kpi)}
                      className="w-full flex items-center justify-between p-2 rounded bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/10 hover:border-purple-500/20 text-left transition-colors duration-150 mb-1"
                    >
                      <span className="text-xs text-purple-300 font-medium">{kpi}</span>
                      {selectedKPIs.includes(kpi) ? (
                        <CheckSquare className="h-3.5 w-3.5 text-purple-400" />
                      ) : (
                        <Square className="h-3.5 w-3.5 text-slate-700" />
                      )}
                    </button>
                  ))}
                </div>
              )}

              {/* Predefined KPIs List */}
              <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider block mb-1">Standard KPIs</span>
              {DEFAULT_KPIS
                .filter(kpi => kpi.toLowerCase().includes(kpiSearch.toLowerCase()))
                .map(kpi => {
                  const isChecked = selectedKPIs.includes(kpi);
                  return (
                    <button
                      key={kpi}
                      onClick={() => toggleKPI(kpi)}
                      className={`w-full flex items-center justify-between p-2 rounded text-left transition-all duration-150 border ${
                        isChecked 
                          ? 'bg-slate-800/40 border-slate-700/60 text-slate-200' 
                          : 'bg-dark-950/30 border-slate-900 text-slate-400 hover:bg-slate-900/20'
                      }`}
                    >
                      <span className="text-xs">{kpi}</span>
                      {isChecked ? (
                        <CheckSquare className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Square className="h-3.5 w-3.5 text-slate-800" />
                      )}
                    </button>
                  );
                })}
            </div>

            {/* Run Extraction Button */}
            <button
              onClick={() => activeDoc && triggerExtraction(activeDoc.id)}
              disabled={!activeDoc || isExtracting || selectedKPIs.length === 0}
              className="mt-4 glow-btn-blue w-full h-10 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold uppercase tracking-wider"
            >
              {isExtracting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Extracting KPIs...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Reprocess Report
                </>
              )}
            </button>
          </div>

        </div>

        {/* Center/Right Columns: Results, Comparisons, Charts (3/4 Columns width) */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          
          {/* Main Workspace Header / Context Summary */}
          {activeDoc ? (
            <div className="glass-card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-dark-900/70 to-blue-950/10">
              <div>
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-400" />
                  <h2 className="text-base font-bold text-white">{activeDoc.filename}</h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Uploaded on {new Date(activeDoc.uploaded_at).toLocaleString()} | Processed {results.length} records.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportExcel}
                  disabled={results.length === 0}
                  className="glow-btn-emerald disabled:opacity-50 disabled:cursor-not-allowed text-xs h-9 px-4"
                >
                  <Download className="h-3.5 w-3.5" />
                  Export formatted Excel
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-card p-10 text-center flex flex-col items-center justify-center bg-dark-900/30 border-dashed">
              <FileText className="h-12 w-12 text-slate-600 mb-3 animate-pulse" />
              <h2 className="text-lg font-semibold text-slate-300">No Annual Report Selected</h2>
              <p className="text-sm text-slate-500 mt-1 max-w-md">
                Please upload a PDF annual report from the left sidebar to start extracting KPIs, compiling comparisons, and generating charts.
              </p>
            </div>
          )}

          {activeDoc && (
            <>
              {/* Module 3: Recharts Charts Panel */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Chart 1: Revenue vs Profit Areas */}
                <div className="glass-card p-5">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-emerald-400" />
                    Revenue & PAT Growth Trends
                  </h3>
                  
                  <div className="h-[220px] w-full">
                    {chartData.length === 0 ? (
                      <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">No chart data available</div>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorPat" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }}
                            itemStyle={{ color: '#94a3b8' }}
                          />
                          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                          {availableKPIsForCharts.includes("Revenue") && (
                            <Area type="monotone" dataKey="Revenue" name="Revenue" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRev)" strokeWidth={2} />
                          )}
                          {availableKPIsForCharts.includes("PAT") && (
                            <Area type="monotone" dataKey="PAT" name="Profit After Tax (PAT)" stroke="#10b981" fillOpacity={1} fill="url(#colorPat)" strokeWidth={2} />
                          )}
                        </AreaChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>

                {/* Chart 2: Custom Selected KPI Trend Line */}
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-purple-400" />
                      KPI Performance Trend
                    </h3>
                    
                    {/* Selector Dropdown */}
                    <select
                      value={activeChartKpi}
                      onChange={(e) => setActiveChartKpi(e.target.value)}
                      className="bg-dark-950 border border-slate-800 rounded text-xs text-slate-300 px-2 py-1 focus:outline-none"
                    >
                      {availableKPIsForCharts.map(kpi => (
                        <option key={kpi} value={kpi}>{kpi}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="h-[220px] w-full">
                    {chartData.length === 0 ? (
                      <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">No chart data available</div>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }}
                            itemStyle={{ color: '#94a3b8' }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey={activeChartKpi} 
                            name={activeChartKpi} 
                            stroke="#8b5cf6" 
                            strokeWidth={3} 
                            activeDot={{ r: 6 }} 
                            dot={{ stroke: '#8b5cf6', strokeWidth: 2, r: 4, fill: '#0b0f19' }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>

              </div>

              {/* Module 4: Comparison Section */}
              <div className="glass-card p-5">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Activity className="h-4 w-4 text-emerald-400" />
                  Financial Analysis (YoY Growth & CAGR)
                </h3>
                
                <div className="overflow-x-auto">
                  {results.length === 0 ? (
                    <p className="text-xs text-slate-500 italic py-2">No comparisons calculated yet. Reprocess to load.</p>
                  ) : (
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="pb-3 font-semibold w-1/4">Financial KPI</th>
                          {chartData.map(y => (
                            <th key={y.name} className="pb-3 font-semibold text-right">{y.name}</th>
                          ))}
                          <th className="pb-3 font-semibold text-right text-emerald-400">YoY Growth (%)</th>
                          <th className="pb-3 font-semibold text-right text-purple-400">CAGR (%)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/50">
                        {comparisonKPIs.map(kpi => {
                          const kpiRows = results.filter(r => r.kpi_name === kpi);
                          // Sort rows to find latest YoY and CAGR
                          const sortedKpiRows = [...kpiRows].sort((a: any, b: any) => {
                            const numA = parseInt(a.fiscal_year.replace(/\D/g, '')) || 0;
                            const numB = parseInt(b.fiscal_year.replace(/\D/g, '')) || 0;
                            return numA - numB;
                          });
                          
                          const latestRow = sortedKpiRows[sortedKpiRows.length - 1];
                          const yoy = latestRow?.yoy_growth;
                          const cagr = latestRow?.cagr;
                          
                          return (
                            <tr key={kpi} className="hover:bg-slate-900/10">
                              <td className="py-3 font-semibold text-slate-200">{kpi}</td>
                              
                              {chartData.map(y => {
                                const yrMatch = kpiRows.find(r => r.fiscal_year === y.name);
                                return (
                                  <td key={y.name} className="py-3 text-right text-slate-400">
                                    {yrMatch ? yrMatch.kpi_value_raw : '-'}
                                  </td>
                                );
                              })}
                              
                              <td className={`py-3 text-right font-medium ${
                                yoy !== null && yoy !== undefined
                                  ? yoy > 0 
                                    ? 'text-emerald-400' 
                                    : yoy < 0 
                                      ? 'text-rose-400' 
                                      : 'text-slate-400'
                                  : 'text-slate-600'
                              }`}>
                                {yoy !== null && yoy !== undefined ? `${yoy}%` : 'N/A'}
                              </td>
                              
                              <td className="py-3 text-right font-medium text-purple-400">
                                {cagr !== null && cagr !== undefined ? `${cagr}%` : 'N/A'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>

              {/* Module 5: Extraction Results Table */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                
                {/* Main Results Table (2/3 Column width) */}
                <div className="xl:col-span-2 glass-card p-5">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                      Extracted KPI Elements
                    </h3>

                    {/* Table Filters */}
                    <div className="flex flex-wrap items-center gap-2">
                      {/* Confidence Filter */}
                      <select
                        value={confidenceFilter}
                        onChange={(e) => setConfidenceFilter(e.target.value)}
                        className="bg-dark-950 border border-slate-800 rounded text-[11px] text-slate-400 px-2.5 py-1 focus:outline-none"
                      >
                        <option value="all">All Confidence Levels</option>
                        <option value="high">High (&gt;= 90%)</option>
                        <option value="medium">Medium (75% - 89%)</option>
                        <option value="low">Low (&lt; 75%)</option>
                      </select>

                      {/* Text Search filter */}
                      <div className="relative">
                        <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-slate-500" />
                        <input 
                          type="text"
                          placeholder="Filter results..."
                          value={tableSearch}
                          onChange={(e) => setTableSearch(e.target.value)}
                          className="bg-dark-950 border border-slate-800 rounded pl-7 pr-2.5 py-1 text-[11px] text-white focus:outline-none focus:border-slate-700 w-[140px] md:w-[180px]"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Results Grid */}
                  <div className="overflow-x-auto">
                    {filteredResults.length === 0 ? (
                      <p className="text-xs text-slate-500 italic py-6 text-center">No matching KPI records found.</p>
                    ) : (
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/20">
                            <th className="p-2.5 font-medium cursor-pointer select-none" onClick={() => handleSort('kpi_name')}>
                              <span className="flex items-center gap-1">
                                KPI Name
                                <ArrowUpDown className="h-3 w-3" />
                              </span>
                            </th>
                            <th className="p-2.5 font-medium cursor-pointer select-none text-center" onClick={() => handleSort('fiscal_year')}>
                              <span className="flex items-center justify-center gap-1">
                                Year
                                <ArrowUpDown className="h-3 w-3" />
                              </span>
                            </th>
                            <th className="p-2.5 font-medium text-right cursor-pointer select-none" onClick={() => handleSort('kpi_value_raw')}>
                              <span className="flex items-center justify-end gap-1">
                                Extracted Value
                                <ArrowUpDown className="h-3 w-3" />
                              </span>
                            </th>
                            <th className="p-2.5 font-medium cursor-pointer select-none text-center" onClick={() => handleSort('confidence')}>
                              <span className="flex items-center justify-center gap-1">
                                Confidence
                                <ArrowUpDown className="h-3 w-3" />
                              </span>
                            </th>
                            <th className="p-2.5 font-medium text-center">Page</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/40">
                          {filteredResults.map(r => (
                            <tr 
                              key={r.id} 
                              onClick={() => setSelectedTrace(r)}
                              className={`cursor-pointer transition-colors duration-150 ${
                                selectedTrace?.id === r.id 
                                  ? 'bg-blue-600/10 hover:bg-blue-600/15' 
                                  : 'hover:bg-slate-900/15'
                              }`}
                            >
                              <td className="p-2.5 font-medium text-slate-200">
                                <span className="flex items-center gap-2">
                                  {r.kpi_name}
                                  {r.is_custom === 1 && (
                                    <span className="text-[9px] px-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-semibold uppercase">Custom</span>
                                  )}
                                </span>
                              </td>
                              <td className="p-2.5 text-center text-slate-400 font-semibold">{r.fiscal_year}</td>
                              <td className="p-2.5 text-right font-bold text-slate-100">{r.kpi_value_raw}</td>
                              <td className="p-2.5 text-center">
                                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${getConfidenceBadge(r.confidence)}`}>
                                  {r.confidence}%
                                </span>
                              </td>
                              <td className="p-2.5 text-center text-slate-400">
                                <span className="underline hover:text-blue-400">P. {r.page_number}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>

                {/* Source Traceability Panel (1/3 Column width) */}
                <div className="xl:col-span-1 flex flex-col">
                  <div className="glass-card p-5 flex-1 flex flex-col bg-gradient-to-tr from-dark-900/80 to-slate-900/50">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                      <Info className="h-4 w-4 text-emerald-400" />
                      Source Traceability
                    </h3>
                    
                    {selectedTrace ? (
                      <div className="flex-1 flex flex-col gap-4">
                        {/* KPI meta info */}
                        <div className="bg-dark-950/60 p-3.5 rounded-lg border border-slate-800/80">
                          <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Selected KPI Element</div>
                          <div className="text-base font-bold text-white mt-0.5 flex items-center gap-2">
                            {selectedTrace.kpi_name}
                            {selectedTrace.is_custom === 1 && (
                              <span className="text-[9px] px-1 rounded bg-purple-500/15 text-purple-400 border border-purple-500/20">CUSTOM</span>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-slate-900">
                            <div>
                              <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Extracted Year</span>
                              <span className="text-sm font-semibold text-slate-200">{selectedTrace.fiscal_year}</span>
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Extracted Value</span>
                              <span className="text-sm font-bold text-emerald-400">{selectedTrace.kpi_value_raw}</span>
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Report Location</span>
                              <span className="text-sm font-medium text-slate-300">Page {selectedTrace.page_number}</span>
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Reliability Score</span>
                              <span className="text-sm font-semibold text-slate-200">{selectedTrace.confidence}%</span>
                            </div>
                          </div>
                        </div>

                        {/* Page highlighted snippet text */}
                        <div className="flex-1 flex flex-col">
                          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-2 block">Extract Source Snippet</span>
                          <div className="flex-1 bg-dark-950 p-4 rounded-lg border border-slate-800/90 text-[11px] leading-relaxed text-slate-300 font-mono overflow-y-auto max-h-[160px] md:max-h-none select-text">
                            {/* Simple text highlight for key concepts */}
                            {(() => {
                              const keyword = selectedTrace.kpi_value_raw;
                              const text = selectedTrace.source_text;
                              if (!keyword || !text) return text;
                              
                              const parts = text.split(new RegExp(`(${reEscape(keyword)})`, 'gi'));
                              return parts.map((part, idx) => 
                                part.toLowerCase() === keyword.toLowerCase() 
                                  ? <mark key={idx} className="bg-emerald-500/20 text-emerald-300 px-0.5 rounded font-bold border border-emerald-500/30">{part}</mark> 
                                  : part
                              );
                            })()}
                          </div>
                        </div>
                        
                        <div className="text-[10px] text-slate-500 flex items-start gap-1">
                          <Sparkles className="h-3 w-3 text-purple-400 mt-0.5 flex-shrink-0" />
                          <span>This record was mapped directly from standard financial tables or sentences using rule-based synonym indexing.</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-lg">
                        <HelpCircle className="h-10 w-10 text-slate-700 mb-2 animate-bounce" />
                        <p className="text-xs text-slate-400 font-medium">Select a KPI from the results list</p>
                        <p className="text-[10px] text-slate-600 mt-1">We will display the source page number and highlight the exact text segment extracted to verify data integrity live.</p>
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </>
          )}

        </div>
      </main>

      {/* Footer Branding */}
      <footer className="w-full border-t border-slate-800 bg-dark-950 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between text-xs text-slate-500 gap-2">
        <p>© 2026 FinExtract. Designed for college innovation summits & investor demos.</p>
        <div className="flex gap-4">
          <a href="#" className="hover:text-slate-300">Architecture Details</a>
          <span>•</span>
          <a href="#" className="hover:text-slate-300">Offline PWA Status</a>
          <span>•</span>
          <a href="#" className="hover:text-slate-300">Electron build v1.0</a>
        </div>
      </footer>
    </div>
  );
}

// Simple regex escaping helper for string highlighting
function reEscape(s: string) {
  return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}
