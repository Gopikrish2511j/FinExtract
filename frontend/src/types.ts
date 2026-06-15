export interface Document {
  id: number;
  filename: string;
  filepath: string;
  uploaded_at: string;
}

export interface ExtractedKPI {
  id: number;
  document_id: number;
  kpi_name: string;
  kpi_value_raw: string;
  kpi_value_numeric: number;
  fiscal_year: string;
  page_number: number;
  source_text: string;
  confidence: number;
  is_custom: number;
  yoy_growth: number | null;
  cagr: number | null;
}
