import os
import subprocess
import sys

# Ensure reportlab is installed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    print("Installing reportlab for sample PDF generation...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

def create_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_annual_report.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=15
    )
    story.append(Paragraph("FinExtract Demo Annual Report (FY23 - FY25)", title_style))
    story.append(Spacer(1, 10))
    
    # Intro
    intro_style = ParagraphStyle(
        'IntroText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=15
    )
    story.append(Paragraph("This sample corporate disclosure statement is generated for system validation. The table below outlines the profit & loss summaries, balance sheet snapshots, and relevant financial ratios across three consecutive fiscal periods.", intro_style))
    story.append(Spacer(1, 8))
    
    # Financial Table data
    data = [
        ["Financial Metric", "FY23", "FY24", "FY25"],
        ["Revenue from Operations", "7,000 Cr", "8,200 Cr", "9,150 Cr"],
        ["Net Sales", "6,800 Cr", "8,000 Cr", "8,950 Cr"],
        ["EBITDA", "1,800 Cr", "2,150 Cr", "2,450 Cr"],
        ["EBIT", "1,500 Cr", "1,800 Cr", "2,050 Cr"],
        ["PAT", "1,200 Cr", "1,550 Cr", "1,916 Cr"],
        ["Net Profit", "1,200 Cr", "1,550 Cr", "1,916 Cr"],
        ["Operating Profit", "1,450 Cr", "1,750 Cr", "1,980 Cr"],
        ["Gross Profit", "3,200 Cr", "3,800 Cr", "4,300 Cr"],
        ["Cash Flow from Operations", "1,400 Cr", "1,650 Cr", "1,850 Cr"],
        ["Total Assets", "12,000 Cr", "14,500 Cr", "16,800 Cr"],
        ["Total Liabilities", "5,000 Cr", "6,000 Cr", "6,500 Cr"],
        ["Inventory", "950 Cr", "1,100 Cr", "1,250 Cr"],
        ["Working Capital", "1,500 Cr", "1,800 Cr", "2,100 Cr"],
        ["EPS", "12.0", "15.5", "19.16"],
        ["Debt To Equity Ratio", "0.41", "0.40", "0.38"]
    ]
    
    t = Table(data, colWidths=[180, 80, 80, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F2937')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F3F4F6'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
        ('TOPPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Notes Section for text extraction validation
    story.append(Paragraph("Extractable Footnotes:", ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1F2937'), spaceAfter=6)))
    
    note_style = ParagraphStyle(
        'NoteText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=6
    )
    story.append(Paragraph("Note 1: Employee Cost for FY25 amounted to 1,120 Cr, marking a steady rise from 980 Cr in FY24.", note_style))
    story.append(Paragraph("Note 2: R&D Cost in FY25 reached 450 Cr, showing expansion from 370 Cr during the prior fiscal term.", note_style))
    
    doc.build(story)
    print(f"Demo PDF report created successfully at:\n{pdf_path}")

if __name__ == '__main__':
    create_pdf()
