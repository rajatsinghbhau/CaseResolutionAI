"""
CaseResolutionAI - Professional PDF Case Dossier Generator
Generates comprehensive, court & mediation ready PDF Case Dossiers using ReportLab.
"""

import io
from datetime import date
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from case_store import calculate_readiness_score
from letter_service import generate_formal_legal_notice


def generate_case_dossier_pdf(case_data: Dict[str, Any]) -> bytes:
    """
    Generates a structured, beautifully formatted PDF Case Dossier.
    Returns the generated PDF as raw bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e3a8a')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    italic_style = ParagraphStyle(
        'Italic_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#475569')
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#78350f')
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("CaseResolutionAI — Consumer Dispute Dossier", title_style))
    today_str = date.today().strftime("%d %B %Y")
    readiness = calculate_readiness_score(case_data)
    elements.append(Paragraph(
        f"Case Dossier Reference: <b>{case_data.get('id', 'N/A')}</b> | Generated: {today_str} | Dossier Completeness: <b>{readiness['score']}/100</b>",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    # 2. Disclaimer Notice Box
    disclaimer_text = (
        "<b>LEGAL NOTICE & ARCHIVE RECORD:</b> This dossier is a structured compilation of consumer-provided records, "
        "statements, and attached documentary evidence. It is prepared for dispute organization and formal communication "
        "with company grievance officers, mediators, or the National Consumer Helpline. It does not constitute formal legal counsel "
        "nor guarantee a specific refund outcome."
    )
    disc_table = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[530])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fefce8')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#facc15')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(disc_table)
    elements.append(Spacer(1, 12))

    # 3. Transaction Summary Table
    elements.append(Paragraph("1. Particulars of Transaction & Grievance", h1_style))
    summary_data = [
        [Paragraph("<b>Product / Service:</b>", body_style), Paragraph(f"{case_data.get('product_name')} ({case_data.get('product_category')})", body_style)],
        [Paragraph("<b>Seller / Platform:</b>", body_style), Paragraph(str(case_data.get('seller_name')), body_style)],
        [Paragraph("<b>Amount Paid:</b>", body_style), Paragraph(f"INR {case_data.get('purchase_amount', 0):,.2f}", body_style)],
        [Paragraph("<b>Purchase Date:</b>", body_style), Paragraph(str(case_data.get('purchase_date')), body_style)],
        [Paragraph("<b>Incident / Delivery:</b>", body_style), Paragraph(str(case_data.get('delivery_date', case_data.get('incident_date'))), body_style)],
        [Paragraph("<b>Support Ticket ID:</b>", body_style), Paragraph(str(case_data.get('support_ticket_ref', 'N/A')), body_style)],
        [Paragraph("<b>Remedy Requested:</b>", body_style), Paragraph(str(case_data.get('relief_sought')), body_style)],
        [Paragraph("<b>Current Status:</b>", body_style), Paragraph(str(case_data.get('status', 'Active')), body_style)],
    ]
    t_summary = Table(summary_data, colWidths=[140, 390])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 14))

    # 4. Consumer Statement (Distinguished)
    elements.append(Paragraph("2. Consumer Statement of Facts (User Narrative)", h1_style))
    clean_statement = case_data.get('user_statement', '').replace('\n', '<br/>')
    statement_para = Paragraph(clean_statement, italic_style)
    st_table = Table([[statement_para]], colWidths=[530])
    st_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(st_table)
    elements.append(Spacer(1, 14))

    # 5. Chronological Incident Timeline Table
    elements.append(Paragraph("3. Chronological Incident Timeline", h1_style))
    timeline = case_data.get('timeline', [])
    if timeline:
        timeline_rows = [[
            Paragraph("<b>Date</b>", body_style),
            Paragraph("<b>Event Milestone</b>", body_style),
            Paragraph("<b>Source</b>", body_style),
            Paragraph("<b>Details</b>", body_style)
        ]]
        for ev in timeline:
            timeline_rows.append([
                Paragraph(str(ev.get('date', '')), body_style),
                Paragraph(str(ev.get('event', '')), body_style),
                Paragraph(str(ev.get('source', '')), body_style),
                Paragraph(str(ev.get('details', '')), body_style)
            ])
        t_time = Table(timeline_rows, colWidths=[75, 120, 100, 235])
        t_time.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t_time)
    else:
        elements.append(Paragraph("No timeline events logged.", body_style))
    elements.append(Spacer(1, 14))

    # 6. Evidence Artifacts Index
    elements.append(Paragraph("4. Evidence & Proof Artifacts Index", h1_style))
    evidence = case_data.get('evidence_items', [])
    valid_ev = [e for e in evidence if e.get('verification_status') not in ['Awaiting User Upload', 'Pending Attachment']]
    if valid_ev:
        ev_rows = [[
            Paragraph("<b>#</b>", body_style),
            Paragraph("<b>File Name</b>", body_style),
            Paragraph("<b>Category</b>", body_style),
            Paragraph("<b>Verification Status</b>", body_style),
            Paragraph("<b>Description</b>", body_style)
        ]]
        for idx, e in enumerate(valid_ev):
            ev_rows.append([
                Paragraph(str(idx + 1), body_style),
                Paragraph(str(e.get('file_name', '')), body_style),
                Paragraph(str(e.get('file_type', '')), body_style),
                Paragraph(str(e.get('verification_status', 'Attached')), body_style),
                Paragraph(str(e.get('description', '')), body_style)
            ])
        t_ev = Table(ev_rows, colWidths=[25, 140, 110, 100, 155])
        t_ev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcfce7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t_ev)
    else:
        elements.append(Paragraph("No physical or digital documents attached to this case yet.", body_style))
    
    # 7. Escalation Next Steps Guide
    elements.append(Spacer(1, 14))
    elements.append(Paragraph("5. Official Redressal Escalation Matrix (India)", h1_style))
    escalation_text = (
        "<b>Level 1: Customer Care</b> — Allow 3 to 7 business days SLA.<br/>"
        "<b>Level 2: Nodal Grievance Redressal Officer</b> — Send formal representation under E-Commerce Rules, 2020.<br/>"
        "<b>Level 3: National Consumer Helpline (NCH / INGRAM)</b> — Toll-Free 1915 / consumerhelpline.gov.in.<br/>"
        "<b>Level 4: e-Daakhil</b> — Online filing before District / State Consumer Commission via edaakhil.nic.in."
    )
    elements.append(Paragraph(escalation_text, body_style))

    # Build the document
    doc.build(elements)
    return buffer.getvalue()

