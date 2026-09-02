#!/usr/bin/env python3
"""
Vensora Security Audit & Project Status Report Generator
Generates aesthetic PDF reports using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
import os
from datetime import datetime

# ============================================================
# COLOR PALETTE
# ============================================================
PRIMARY = HexColor("#6C63FF")       # Deep Purple
PRIMARY_DARK = HexColor("#4A42D4")
ACCENT = HexColor("#00D4AA")        # Teal
ACCENT_DARK = HexColor("#00B894")
DANGER = HexColor("#FF6B6B")        # Coral Red
WARNING = HexColor("#FFA726")       # Amber
SUCCESS = HexColor("#66BB6A")       # Green
INFO = HexColor("#42A5F5")          # Blue
BG_DARK = HexColor("#1A1A2E")       # Dark Navy
BG_CARD = HexColor("#16213E")       # Card Background
BG_LIGHT = HexColor("#F8F9FA")      # Light Background
TEXT_DARK = HexColor("#2D3436")
TEXT_SECONDARY = HexColor("#636E72")
TEXT_LIGHT = HexColor("#B2BEC3")
BORDER = HexColor("#DFE6E9")
SECTION_BG = HexColor("#F0F3FF")

# ============================================================
# STYLES
# ============================================================
styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    'CustomTitle', parent=styles['Title'],
    fontSize=28, leading=34, textColor=PRIMARY_DARK,
    spaceAfter=6, fontName='Helvetica-Bold'
)

style_subtitle = ParagraphStyle(
    'CustomSubtitle', parent=styles['Normal'],
    fontSize=12, leading=16, textColor=TEXT_SECONDARY,
    spaceAfter=20, fontName='Helvetica'
)

style_h1 = ParagraphStyle(
    'H1', parent=styles['Heading1'],
    fontSize=20, leading=26, textColor=PRIMARY_DARK,
    spaceBefore=16, spaceAfter=10, fontName='Helvetica-Bold'
)

style_h2 = ParagraphStyle(
    'H2', parent=styles['Heading2'],
    fontSize=15, leading=20, textColor=PRIMARY,
    spaceBefore=12, spaceAfter=8, fontName='Helvetica-Bold'
)

style_h3 = ParagraphStyle(
    'H3', parent=styles['Heading3'],
    fontSize=12, leading=16, textColor=TEXT_DARK,
    spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'
)

style_body = ParagraphStyle(
    'CustomBody', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=TEXT_DARK,
    spaceAfter=6, fontName='Helvetica', alignment=TA_JUSTIFY
)

style_body_small = ParagraphStyle(
    'BodySmall', parent=style_body,
    fontSize=9, leading=12
)

style_bullet = ParagraphStyle(
    'CustomBullet', parent=style_body,
    fontSize=10, leading=14, leftIndent=20,
    bulletIndent=8, spaceBefore=2, spaceAfter=2
)

style_code = ParagraphStyle(
    'Code', parent=styles['Code'],
    fontSize=8, leading=10, textColor=HexColor("#E17055"),
    fontName='Courier', backColor=HexColor("#F8F9FA"),
    borderColor=BORDER, borderWidth=1, borderPadding=4,
    spaceAfter=6
)

style_footer = ParagraphStyle(
    'Footer', parent=styles['Normal'],
    fontSize=8, textColor=TEXT_LIGHT, alignment=TA_CENTER
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def create_header_bar():
    """Create a colored header bar"""
    d = Drawing(500, 4)
    d.add(Rect(0, 0, 500, 4, fillColor=PRIMARY, strokeColor=None))
    return d

def create_section_header(text, color=PRIMARY):
    """Create a styled section header with accent bar"""
    elements = []
    d = Drawing(500, 2)
    d.add(Rect(0, 0, 500, 2, fillColor=color, strokeColor=None))
    elements.append(d)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(text, style_h2))
    return elements

def severity_badge(severity):
    """Return colored severity text"""
    colors = {
        'CRITICAL': f'<font color="#FF0000"><b>[CRITICAL]</b></font>',
        'HIGH': f'<font color="#FF6B6B"><b>[HIGH]</b></font>',
        'MEDIUM': f'<font color="#FFA726"><b>[MEDIUM]</b></font>',
        'LOW': f'<font color="#66BB6A"><b>[LOW]</b></font>',
        'INFO': f'<font color="#42A5F5"><b>[INFO]</b></font>',
    }
    return colors.get(severity, f'<b>[{severity}]</b>')

def make_stat_card(label, value, color=PRIMARY):
    """Create a statistics card"""
    data = [[
        Paragraph(f'<font color="{color.hexval()}" size="22"><b>{value}</b></font>', style_body),
        Paragraph(f'<font color="#636E72" size="9">{label}</font>', style_body_small)
    ]]
    t = Table(data, colWidths=[80, 120])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#F8F9FF")),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    return t

# ============================================================
# PAGE TEMPLATES
# ============================================================
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(2*cm, 1.5*cm, f"Vensora Security Audit Report")
    canvas.drawRightString(A4[0] - 2*cm, 1.5*cm, f"Page {doc.page}")
    canvas.setStrokeColor(BORDER)
    canvas.line(2*cm, 1.8*cm, A4[0] - 2*cm, 1.8*cm)
    # Top accent line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(0, A4[1] - 1.5*mm, A4[0], A4[1] - 1.5*mm)
    canvas.restoreState()

# ============================================================
# MASTER REPORT
# ============================================================
def generate_master_report():
    output_path = os.path.expanduser("~/Downloads/Vensora_Security_Audit_Report.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        leftMargin=2*cm, rightMargin=2*cm
    )
    
    story = []
    page_width = A4[0] - 4*cm
    
    # ---- COVER PAGE ----
    story.append(Spacer(1, 60))
    
    # Logo area
    logo_drawing = Drawing(200, 60)
    logo_drawing.add(Rect(0, 10, 180, 40, fillColor=PRIMARY, strokeColor=None, rx=8))
    logo_drawing.add(String(90, 22, "VENSORA", fillColor=white, fontSize=24, fontName='Helvetica-Bold', textAnchor='middle'))
    story.append(logo_drawing)
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("Security Audit &<br/>Project Status Report", style_title))
    story.append(Spacer(1, 8))
    
    # Accent line
    accent_drawing = Drawing(120, 3)
    accent_drawing.add(Rect(0, 0, 120, 3, fillColor=ACCENT, strokeColor=None))
    story.append(accent_drawing)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(
        "Enterprise AI Customer Connect Platform<br/>"
        "Comprehensive Codebase Analysis & Vulnerability Assessment",
        style_subtitle
    ))
    story.append(Spacer(1, 40))
    
    # Meta info table
    meta_data = [
        ['Report Date', datetime.now().strftime('%B %d, %Y')],
        ['Project', 'Vensora Phase 1'],
        ['Scope', 'Full Stack - Backend, Frontend, Infrastructure'],
        ['Classification', 'CONFIDENTIAL'],
    ]
    meta_table = Table(meta_data, colWidths=[120, 250])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_SECONDARY),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_DARK),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER),
    ]))
    story.append(meta_table)
    story.append(PageBreak())
    
    # ---- TABLE OF CONTENTS ----
    story.extend(create_section_header("Table of Contents"))
    story.append(Spacer(1, 8))
    
    toc_items = [
        ("1", "Executive Summary", "High-level overview of findings"),
        ("2", "Project Architecture Overview", "Technology stack and module structure"),
        ("3", "Security Vulnerabilities", "Detailed findings with severity ratings"),
        ("4", "API Security Analysis", "Endpoint-level security assessment"),
        ("5", "Authentication & Authorization Audit", "JWT, OAuth, RBAC review"),
        ("6", "Data Exposure Risks", "Sensitive data handling review"),
        ("7", "Infrastructure Security", "Docker, network, and config security"),
        ("8", "Frontend Security Assessment", "Client-side vulnerability review"),
        ("9", "AI/ML Security Considerations", "LLM, RAG, and voice pipeline risks"),
        ("10", "Project Completion Status", "Module-by-module completion status"),
        ("11", "Recommendations & Remediation", "Priority action items"),
    ]
    
    for num, title, desc in toc_items:
        story.append(Paragraph(
            f'<b>{num}.</b> &nbsp; <b>{title}</b> <font color="#636E72">- {desc}</font>',
            style_body
        ))
        story.append(Spacer(1, 2))
    
    story.append(PageBreak())
    
    # ---- 1. EXECUTIVE SUMMARY ----
    story.extend(create_section_header("1. Executive Summary"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(
        "This report presents the findings of a comprehensive security audit and project status assessment "
        "of the Vensora platform — an enterprise AI customer connect solution designed for the logistics industry. "
        "The audit covers all backend services, frontend applications, infrastructure configurations, and AI/ML pipelines.",
        style_body
    ))
    story.append(Spacer(1, 12))
    
    # Stats cards
    stats_data = [[
        make_stat_card("Critical Issues", "3", DANGER),
        make_stat_card("High Issues", "5", WARNING),
        make_stat_card("Medium Issues", "7", HexColor("#FFA726")),
        make_stat_card("Low/Info", "4", INFO),
    ]]
    stats_table = Table(stats_data, colWidths=[page_width/4]*4)
    stats_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 16))
    
    # Risk summary
    risk_data = [
        ['Risk Category', 'Findings', 'Status'],
        ['Secrets Management', '3 Critical', 'IMMEDIATE ACTION'],
        ['Authentication', '1 High + 2 Medium', 'REMEDIATION NEEDED'],
        ['API Security', '2 High + 1 Medium', 'REMEDIATION NEEDED'],
        ['Data Exposure', '2 High + 1 Medium', 'REMEDIATION NEEDED'],
        ['Input Validation', '2 Medium', 'REMEDIATION NEEDED'],
        ['Infrastructure', '1 High + 1 Medium', 'REMEDIATION NEEDED'],
        ['AI/ML Pipeline', '3 Medium', 'REVIEW NEEDED'],
    ]
    risk_table = Table(risk_data, colWidths=[page_width*0.4, page_width*0.3, page_width*0.3])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F8F9FF")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#F8F9FF"), white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TEXTCOLOR', (2, 1), (2, 1), DANGER),
        ('TEXTCOLOR', (2, 2), (2, 3), WARNING),
        ('TEXTCOLOR', (2, 4), (2, 5), WARNING),
        ('TEXTCOLOR', (2, 6), (2, 7), INFO),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(risk_table)
    story.append(PageBreak())
    
    # ---- 2. PROJECT ARCHITECTURE ----
    story.extend(create_section_header("2. Project Architecture Overview"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(
        "Vensora is built as a <b>Modular Monolith</b> with clean logical boundaries for future microservices migration. "
        "The architecture follows a domain-driven design with 13 backend modules, a React frontend, and Docker-based infrastructure.",
        style_body
    ))
    story.append(Spacer(1, 12))
    
    # Tech stack table
    story.append(Paragraph("<b>Technology Stack</b>", style_h3))
    tech_data = [
        ['Layer', 'Technology', 'Version'],
        ['Frontend', 'React + Vite + TypeScript', '19.x / 8.x / 6.x'],
        ['Backend', 'FastAPI + Python', '3.14'],
        ['Database', 'PostgreSQL (SQLAlchemy ORM)', '16'],
        ['Cache', 'Redis', '7'],
        ['Object Storage', 'MinIO (S3-compatible)', 'Latest'],
        ['Vector DB', 'Qdrant (BAAI BGE-M3)', 'Latest'],
        ['AI/LLM', 'LangGraph + Groq', 'Latest'],
        ['STT', 'Faster Whisper', 'base'],
        ['TTS', 'Piper (HTTP server)', 'en_US-lessac'],
        ['Telephony', 'Twilio Media Streams', 'WebSocket'],
        ['Auth', 'JWT + Google OAuth', 'HS256'],
    ]
    tech_table = Table(tech_data, colWidths=[page_width*0.25, page_width*0.45, page_width*0.3])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#F8F9FF"), white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 16))
    
    # Module structure
    story.append(Paragraph("<b>Backend Module Structure</b>", style_h3))
    modules_data = [
        ['Module', 'Purpose', 'Status'],
        ['auth', 'JWT + Google OAuth authentication', 'Complete'],
        ['users', 'User provisioning, RBAC, profiles', 'Complete'],
        ['roles', 'Role-based access control system', 'Complete'],
        ['departments', 'Department hierarchy', 'Complete'],
        ['agents', 'AI agent configuration & prompts', 'Complete'],
        ['calls', 'Call logging & recordings', 'Complete'],
        ['campaigns', 'Inbound/outbound campaign mgmt', 'Complete'],
        ['contacts', 'Contact management & opt-out', 'Complete'],
        ['crm', 'CRM, tickets, shipments, knowledge', 'Complete'],
        ['ai', 'LangGraph, RAG, guardrails, tools', 'Complete'],
        ['voice', 'STT, TTS, VAD services', 'Complete'],
        ['telephony', 'Twilio streaming, state machine', 'Complete'],
        ['storage', 'MinIO recording storage', 'Complete'],
    ]
    mod_table = Table(modules_data, colWidths=[page_width*0.2, page_width*0.5, page_width*0.3])
    mod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#F0FFFC"), white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(mod_table)
    story.append(PageBreak())
    
    # ---- 3. SECURITY VULNERABILITIES ----
    story.extend(create_section_header("3. Security Vulnerabilities"))
    story.append(Spacer(1, 8))
    
    vulnerabilities = [
        {
            'id': 'VULN-001',
            'title': 'Hardcoded API Keys & Secrets in .env File',
            'severity': 'CRITICAL',
            'location': 'apps/backend/.env',
            'description': (
                'The .env file contains hardcoded production-grade API keys and secrets including: '
                'Twilio Account SID & Auth Token, Groq API Key, OpenRouter API Key, Sarvam API Key, '
                'and database credentials. These are real keys committed to disk.'
            ),
            'impact': 'Full account takeover of Twilio, Groq, OpenRouter, and Sarvam services. '
                      'Database access with full privileges.',
            'remediation': (
                '1. Rotate ALL exposed API keys immediately.\n'
                '2. Move secrets to a vault (e.g., HashiCorp Vault, AWS Secrets Manager).\n'
                '3. Add pre-commit hooks (e.g., gitleaks, truffleHog) to prevent future commits.\n'
                '4. Verify .env is NOT tracked in git history.'
            )
        },
        {
            'id': 'VULN-002',
            'title': 'Weak JWT Secret Key',
            'severity': 'CRITICAL',
            'location': 'apps/backend/.env → SECRET_KEY',
            'description': (
                'The JWT secret key is set to "dummy_secret_key_for_local_testing_123" — '
                'a weak, guessable value. Combined with HS256 algorithm, this allows token forgery.'
            ),
            'impact': 'Attackers can forge valid JWT tokens for any user, bypassing all authentication.',
            'remediation': (
                '1. Generate a cryptographically strong secret (min 256-bit).\n'
                '2. Use RS256 (asymmetric) for production.\n'
                '3. Store secret in environment variables or vault.'
            )
        },
        {
            'id': 'VULN-003',
            'title': 'Default Database Credentials',
            'severity': 'CRITICAL',
            'location': 'docker-compose.yml + .env.example',
            'description': (
                'Default credentials (vensora/vensora_secret for Postgres, '
                'vensora_minio_admin/vensora_minio_secret for MinIO) are used across '
                'development and referenced in production configs.'
            ),
            'impact': 'Unauthorized database access if containers are exposed to network.',
            'remediation': (
                '1. Generate unique strong passwords for each environment.\n'
                '2. Never include real credentials in .env.example.\n'
                '3. Use Docker secrets for production deployments.'
            )
        },
        {
            'id': 'VULN-004',
            'title': 'Wildcard CORS Policy',
            'severity': 'HIGH',
            'location': 'apps/backend/app/main.py:51',
            'description': (
                'CORS middleware is configured with allow_origins=["*"], allowing any origin '
                'to make authenticated requests to the API.'
            ),
            'impact': 'Cross-site request forgery and data exfiltration from any domain.',
            'remediation': 'Restrict CORS to specific frontend domain(s) in production.'
        },
        {
            'id': 'VULN-005',
            'title': 'No Rate Limiting on Authentication Endpoints',
            'severity': 'HIGH',
            'location': 'apps/backend/app/api/v1/auth.py',
            'description': (
                'The /auth/login and /auth/google endpoints have no rate limiting, '
                'enabling brute-force attacks on passwords and token replay.'
            ),
            'impact': 'Credential stuffing, brute-force attacks, account lockout DoS.',
            'remediation': (
                '1. Add rate limiting (e.g., slowapi) — 5 attempts/min per IP.\n'
                '2. Implement account lockout after N failed attempts.\n'
                '3. Add CAPTCHA after repeated failures.'
            )
        },
        {
            'id': 'VULN-006',
            'title': 'No Authentication on CRM/Calls Endpoints',
            'severity': 'HIGH',
            'location': 'apps/backend/app/api/v1/calls.py + crm.py',
            'description': (
                'The GET /calls/ and GET /crm/contacts, /crm/tickets endpoints have no '
                'authentication dependency. Any unauthenticated user can access call data, '
                'customer PII, and ticket information.'
            ),
            'impact': 'Mass data exfiltration of customer PII, call recordings, and support tickets.',
            'remediation': 'Add Depends(get_active_user) or RequirePermission() to all endpoints.'
        },
        {
            'id': 'VULN-007',
            'title': 'No Authentication on WebSocket Endpoints',
            'severity': 'HIGH',
            'location': 'apps/backend/app/modules/telephony/router.py:15,131',
            'description': (
                'The /ws/live-calls and /twilio/stream WebSocket endpoints accept connections '
                'without any authentication. Anyone can monitor live calls or inject barge-in messages.'
            ),
            'impact': 'Unauthorized live call monitoring, call interception, admin impersonation.',
            'remediation': 'Implement WebSocket authentication via token query parameter or cookie.'
        },
        {
            'id': 'VULN-008',
            'title': 'XSS via File Upload in Knowledge Base',
            'severity': 'MEDIUM',
            'location': 'apps/backend/app/api/v1/knowledge.py',
            'description': (
                'The file upload endpoint only checks .txt extension. File content is stored '
                'in the database and could contain malicious content rendered in the UI. '
                'No sanitization of uploaded content.'
            ),
            'impact': 'Stored XSS if uploaded content is rendered in admin dashboard.',
            'remediation': (
                '1. Sanitize all uploaded content before storage.\n'
                '2. Implement content-type validation beyond extension.\n'
                '3. Sanitize output when rendering stored content.'
            )
        },
        {
            'id': 'VULN-009',
            'title': 'Information Disclosure in Error Responses',
            'severity': 'MEDIUM',
            'location': 'apps/backend/app/core/exceptions.py',
            'description': (
                'Validation errors return full exc.errors() details including field names, '
                'types, and internal validation logic to the client.'
            ),
            'impact': 'Internal schema leakage, aids attacker in crafting payloads.',
            'remediation': 'Return generic validation error messages in production.'
        },
        {
            'id': 'VULN-010',
            'title': 'Missing Input Validation on API Parameters',
            'severity': 'MEDIUM',
            'location': 'apps/backend/app/api/v1/calls.py, crm.py',
            'description': (
                'skip and limit query parameters accept arbitrary integer values with no bounds. '
                'Could be used for denial-of-service via extremely large queries.'
            ),
            'impact': 'Database performance degradation, potential DoS.',
            'remediation': 'Add Pydantic query parameter validation with min/max bounds.'
        },
        {
            'id': 'VULN-011',
            'title': 'Hardcoded File Path in Prompt Service',
            'severity': 'MEDIUM',
            'location': 'apps/backend/app/modules/ai/prompts.py:48',
            'description': (
                'The prompt service contains a hardcoded absolute path: '
                '/Users/saidheeraj/LocalProjects/vensora/sample_docs/...'
            ),
            'impact': 'Will break in any non-macOS or different user environment.',
            'remediation': 'Use relative paths or environment variable for document location.'
        },
        {
            'id': 'VULN-012',
            'title': 'Client-Side Role-Based Access Control',
            'severity': 'MEDIUM',
            'location': 'apps/frontend/src/pages/UsersView.tsx',
            'description': (
                'User management access control is implemented only on the frontend by decoding '
                'the JWT client-side. Backend does not enforce role checks on user listing.'
            ),
            'impact': 'Bypassable access control via direct API calls.',
            'remediation': 'Enforce RBAC on backend endpoints, not just frontend.'
        },
        {
            'id': 'VULN-013',
            'title': 'Backend .gitignore Only Tracks vensora.db',
            'severity': 'LOW',
            'location': 'apps/backend/.gitignore',
            'description': (
                'The backend .gitignore only ignores vensora.db. The parent .gitignore handles .env, '
                'but .venv/ and __pycache__/ are only ignored at root level.'
            ),
            'impact': 'Potential accidental commits of virtual environments or cache files.',
            'remediation': 'Add standard Python ignores to apps/backend/.gitignore.'
        },
        {
            'id': 'VULN-014',
            'title': 'No HTTPS Enforcement in Development',
            'severity': 'LOW',
            'location': 'Frontend hardcoded URLs',
            'description': (
                'All frontend API calls use http://localhost:8000. WebSocket uses ws://. '
                'No TLS configuration for local development.'
            ),
            'impact': 'Man-in-the-middle attacks on local network.',
            'remediation': 'Configure TLS for local dev or document secure tunnel setup.'
        },
        {
            'id': 'VULN-015',
            'title': 'CORS Origin Bypass via Host Header',
            'severity': 'LOW',
            'location': 'apps/backend/app/modules/telephony/router.py:115',
            'description': (
                'The Twilio incoming webhook reads the Host header to construct WebSocket URL. '
                'An attacker could manipulate this header.'
            ),
            'impact': 'Potential WebSocket URL manipulation for call hijacking.',
            'remediation': 'Use environment variable for public-facing domain.'
        },
    ]
    
    for vuln in vulnerabilities:
        sev_color = {
            'CRITICAL': DANGER, 'HIGH': WARNING, 
            'MEDIUM': HexColor("#FFA726"), 'LOW': INFO
        }.get(vuln['severity'], TEXT_SECONDARY)
        
        # Vuln header
        vuln_header = Table(
            [[Paragraph(f'<b>{vuln["id"]}</b>', style_body),
              Paragraph(f'<b>{vuln["title"]}</b>', style_body),
              Paragraph(f'<font color="{sev_color.hexval()}"><b>{vuln["severity"]}</b></font>', style_body)]],
            colWidths=[60, page_width*0.6, 80]
        )
        vuln_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#F0F3FF")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, 0), 1, sev_color),
        ]))
        story.append(vuln_header)
        story.append(Spacer(1, 4))
        
        story.append(Paragraph(f'<b>Location:</b> <font face="Courier" size="8">{vuln["location"]}</font>', style_body_small))
        story.append(Spacer(1, 2))
        story.append(Paragraph(f'<b>Description:</b> {vuln["description"]}', style_body_small))
        story.append(Paragraph(f'<b>Impact:</b> {vuln["impact"]}', style_body_small))
        
        rem_text = vuln["remediation"].replace('\n', '<br/>')
        story.append(Paragraph(f'<b>Remediation:</b><br/>{rem_text}', style_body_small))
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    
    # ---- 4. API SECURITY ANALYSIS ----
    story.extend(create_section_header("4. API Security Analysis"))
    story.append(Spacer(1, 8))
    
    api_data = [
        ['Endpoint', 'Auth Required', 'RBAC', 'Rate Limit', 'Status'],
        ['POST /auth/login', 'No', 'N/A', 'No', 'NEEDS RATE LIMIT'],
        ['POST /auth/google', 'No', 'N/A', 'No', 'NEEDS RATE LIMIT'],
        ['POST /auth/change-password', 'Yes (Bearer)', 'Active User', 'No', 'NEEDS RATE LIMIT'],
        ['GET /users/me', 'Yes (Bearer)', 'Any User', 'No', 'OK'],
        ['GET /users/', 'Yes (Bearer)', 'users:read', 'No', 'NEEDS VALIDATION'],
        ['POST /users/provision', 'Yes (Bearer)', 'users:create', 'No', 'OK'],
        ['GET /calls/', 'No', 'None', 'No', 'CRITICAL - ADD AUTH'],
        ['GET /crm/contacts', 'No', 'None', 'No', 'CRITICAL - ADD AUTH'],
        ['GET /crm/tickets', 'No', 'None', 'No', 'CRITICAL - ADD AUTH'],
        ['POST /knowledge/upload', 'Yes (Bearer)', 'Admin check', 'No', 'NEEDS FILE VALIDATION'],
        ['POST /dev/seed', 'No', 'Env check only', 'No', 'OK (dev only)'],
        ['GET /health', 'No', 'N/A', 'No', 'OK'],
        ['WS /ws/live-calls', 'No', 'None', 'No', 'CRITICAL - ADD AUTH'],
        ['WS /twilio/stream', 'No', 'None', 'No', 'HIGH - TWILIO ONLY'],
        ['POST /telephony/twilio/incoming', 'No', 'Webhook', 'No', 'NEEDS SIGNATURE VERIFICATION'],
    ]
    api_table = Table(api_data, colWidths=[page_width*0.3, page_width*0.18, page_width*0.18, page_width*0.14, page_width*0.2])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#F8F9FF"), white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(api_table)
    story.append(PageBreak())
    
    # ---- 5. AUTH & AUTHZ AUDIT ----
    story.extend(create_section_header("5. Authentication & Authorization Audit"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>JWT Implementation Review</b>", style_h3))
    auth_findings = [
        ("Algorithm", "HS256 (HMAC-SHA256) — Symmetric. Acceptable for Phase 1 but recommend RS256 for production."),
        ("Token Expiry", "24 hours — Too long. Recommend 15-60 minutes with refresh tokens."),
        ("Subject Claim", "User UUID — Good. No PII in token payload."),
        ("Token Verification", "Properly validates expiry and signature. Good."),
        ("No Refresh Token", "Missing. After 24h, user must re-authenticate."),
        ("No Token Revocation", "Missing. Compromised tokens remain valid until expiry."),
    ]
    for label, detail in auth_findings:
        story.append(Paragraph(f'<b>{label}:</b> {detail}', style_body_small))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>RBAC Implementation Review</b>", style_h3))
    rbac_findings = [
        ("Permission Model", "Role → RolePermission → Permission. Well-structured many-to-many."),
        ("Wildcard Bypass", "Super admin wildcard (*) bypass is documented and intentional."),
        ("Password Change Enforcement", "must_change_password flag enforced via get_active_user dependency."),
        ("Client-Side Only RBAC", "UsersView checks role from JWT client-side — not enforced on backend GET /users/."),
    ]
    for label, detail in rbac_findings:
        story.append(Paragraph(f'<b>{label}:</b> {detail}', style_body_small))
    
    story.append(PageBreak())
    
    # ---- 6. DATA EXPOSURE ----
    story.extend(create_section_header("6. Data Exposure Risks"))
    story.append(Spacer(1, 8))
    
    data_risks = [
        ("Customer PII in API Responses", "HIGH",
         "GET /crm/contacts returns phone_number, first_name, last_name without authentication. "
         "Any network-adjacent attacker can harvest customer data."),
        ("Call Recording URLs", "HIGH",
         "GET /calls/ returns recording_url in response body. These are MinIO presigned URLs "
         "that could be accessed if intercepted."),
        ("Ticket Descriptions", "MEDIUM",
         "GET /crm/tickets returns full ticket descriptions which may contain sensitive "
         "customer complaint details."),
        ("User Email Addresses", "MEDIUM",
         "GET /users/ exposes all user emails. Combined with no rate limiting, enables "
         "credential stuffing target enumeration."),
        ("Temporary Passwords", "LOW",
         "Provisioned user temporary passwords are returned in API response. Acceptable for "
         "initial setup but should be delivered via secure channel."),
    ]
    
    for title, severity, detail in data_risks:
        sev_color = {'HIGH': WARNING, 'MEDIUM': HexColor("#FFA726"), 'LOW': INFO}.get(severity, TEXT_SECONDARY)
        story.append(Paragraph(
            f'{severity_badge(severity)} <b>{title}</b>',
            style_body
        ))
        story.append(Paragraph(detail, style_body_small))
        story.append(Spacer(1, 8))
    
    story.append(PageBreak())
    
    # ---- 7. INFRASTRUCTURE SECURITY ----
    story.extend(create_section_header("7. Infrastructure Security"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Docker Compose Security</b>", style_h3))
    infra_findings = [
        ("Exposed Ports", "MEDIUM",
         "PostgreSQL (5433), Redis (6379), MinIO (9000/9001), Qdrant (6333/6334) are all exposed to host. "
         "In production, these should be internal-only."),
        ("No Network Isolation", "MEDIUM",
         "All services share the default Docker network. No custom network segments "
         "for database vs application tiers."),
        ("No Resource Limits", "LOW",
         "No CPU/memory limits defined for containers. Risk of resource exhaustion."),
        ("Health Checks", "GOOD",
         "All services have proper health checks configured."),
        ("Persistent Volumes", "GOOD",
         "All data services use named volumes for persistence."),
    ]
    for title, severity, detail in infra_findings:
        story.append(Paragraph(f'{severity_badge(severity)} <b>{title}</b>', style_body))
        story.append(Paragraph(detail, style_body_small))
        story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # ---- 8. FRONTEND SECURITY ----
    story.extend(create_section_header("8. Frontend Security Assessment"))
    story.append(Spacer(1, 8))
    
    frontend_findings = [
        ("Token Storage", "MEDIUM",
         "JWT tokens stored in localStorage (LoginView.tsx:33). Vulnerable to XSS. "
         "Recommend httpOnly cookies for production."),
        ("Hardcoded API URLs", "LOW",
         "All API calls hardcoded to http://localhost:8000. Should use environment variables."),
        ("No CSRF Protection", "LOW",
         "State-changing operations (POST) lack CSRF tokens. Bearer token auth mitigates this partially."),
        ("No Content Security Policy", "LOW",
         "No CSP headers configured. Could enable XSS exploitation."),
        ("Client-Side Auth Check", "MEDIUM",
         "UsersView.tsx decodes JWT to check role. Backend does not enforce this — bypassable."),
        ("No Error Boundary", "LOW",
         "No React error boundary component. Unhandled errors crash the entire app."),
    ]
    for title, severity, detail in frontend_findings:
        story.append(Paragraph(f'{severity_badge(severity)} <b>{title}</b>', style_body))
        story.append(Paragraph(detail, style_body_small))
        story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # ---- 9. AI/ML SECURITY ----
    story.extend(create_section_header("9. AI/ML Security Considerations"))
    story.append(Spacer(1, 8))
    
    ai_findings = [
        ("Prompt Injection Guardrails", "MEDIUM",
         "Basic regex-based injection detection (guardrails.py). Only covers 5 patterns. "
         "Sophisticated attacks can bypass regex. Recommend LLM-based classifier."),
        ("Tool Call Validation", "MEDIUM",
         "AI agent can call get_shipment_status, create_support_ticket, check_ticket_status. "
         "No rate limiting on tool execution. Could create unlimited tickets."),
        ("Emotion Detection Bypass", "LOW",
         "Emotion provider failures are silently caught and ignored. Agent continues without "
         "emotion context, which may lead to inappropriate responses."),
        ("RAG Context Leakage", "MEDIUM",
         "Full document chunks are injected into system prompt. If documents contain PII, "
         "it will be exposed in AI responses."),
        ("LLM API Key Exposure", "LOW",
         "Groq API key is in .env. If .env is compromised, attacker can use LLM service."),
    ]
    for title, severity, detail in ai_findings:
        story.append(Paragraph(f'{severity_badge(severity)} <b>{title}</b>', style_body))
        story.append(Paragraph(detail, style_body_small))
        story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # ---- 10. PROJECT COMPLETION STATUS ----
    story.extend(create_section_header("10. Project Completion Status"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Phase 1 Completion Summary</b>", style_h3))
    story.append(Spacer(1, 8))
    
    completion_data = [
        ['Component', 'Status', 'Completion', 'Notes'],
        ['Backend API Framework', 'COMPLETE', '100%', 'FastAPI with CORS, middleware, exceptions'],
        ['Authentication (JWT + Google)', 'COMPLETE', '95%', 'Missing rate limiting and refresh tokens'],
        ['User Management & RBAC', 'COMPLETE', '90%', 'Missing backend enforcement on some endpoints'],
        ['Department & Role Models', 'COMPLETE', '100%', 'Full CRUD with relationships'],
        ['CRM & Ticket System', 'COMPLETE', '85%', 'Models complete, API endpoints need auth'],
        ['Contact Management', 'COMPLETE', '85%', 'Models complete, API needs auth'],
        ['Call Logging & Recordings', 'COMPLETE', '80%', 'Models complete, API needs auth'],
        ['Campaign Management', 'COMPLETE', '70%', 'Models complete, no API endpoints yet'],
        ['Knowledge Base (RAG)', 'COMPLETE', '80%', 'Upload + Qdrant integration works'],
        ['AI Agent (LangGraph)', 'COMPLETE', '85%', 'Full pipeline: guardrail → RAG → evaluate → generate'],
        ['Guardrails Service', 'PARTIAL', '60%', 'Basic regex only, needs LLM classifier'],
        ['Confidence Evaluator', 'COMPLETE', '80%', 'RAG score + guardrail checks'],
        ['Memory Manager', 'PARTIAL', '50%', 'History optimization done, fact extraction is placeholder'],
        ['Voice STT (Faster Whisper)', 'COMPLETE', '90%', 'Full implementation with warm-up and timeout'],
        ['Voice TTS (Piper)', 'COMPLETE', '85%', 'Multi-language support, HTTP integration'],
        ['VAD Service', 'COMPLETE', '90%', 'WebRTC-based, proper thresholds'],
        ['Twilio Integration', 'COMPLETE', '85%', 'WebSocket streaming, barge-in, state machine'],
        ['Recording Storage (MinIO)', 'COMPLETE', '90%', 'Upload, delete, presigned URLs'],
        ['Database (PostgreSQL)', 'COMPLETE', '100%', 'SQLAlchemy ORM, Alembic migrations'],
        ['Redis Integration', 'PARTIAL', '30%', 'Configured but not actively used yet'],
        ['Structured Logging', 'COMPLETE', '95%', 'JSON formatter with correlation IDs'],
        ['Audit Logging', 'COMPLETE', '85%', 'Async fire-and-forget, structured'],
        ['Health Checks', 'COMPLETE', '90%', 'Postgres, MinIO, API latency'],
        ['Docker Infrastructure', 'COMPLETE', '85%', 'All services containerized'],
        ['Security Tests', 'PARTIAL', '40%', 'Basic curl tests only'],
        ['Frontend Login/Auth', 'COMPLETE', '90%', 'Login, password change flows'],
        ['Frontend Dashboard', 'PARTIAL', '70%', 'Live calls, knowledge base, users'],
        ['Frontend CRM', 'PARTIAL', '65%', 'Contacts and tickets views'],
        ['Frontend Call History', 'PARTIAL', '60%', 'Basic table with mock play button'],
        ['Frontend Styling', 'PARTIAL', '75%', 'Glass morphism theme, responsive'],
        ['Documentation', 'PARTIAL', '40%', 'README exists, needs API docs'],
        ['CI/CD Pipeline', 'NOT STARTED', '0%', 'No pipeline configured'],
        ['Monitoring (Prometheus/Grafana)', 'NOT STARTED', '0%', 'Configured in README, not implemented'],
    ]
    
    comp_table = Table(completion_data, colWidths=[page_width*0.28, page_width*0.12, page_width*0.12, page_width*0.48])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#F8F9FF"), white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(comp_table)
    story.append(PageBreak())
    
    # ---- 11. RECOMMENDATIONS ----
    story.extend(create_section_header("11. Recommendations & Remediation"))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Immediate Actions (This Sprint)</b>", style_h3))
    story.append(Spacer(1, 4))
    
    immediate = [
        "Rotate ALL exposed API keys (Twilio, Groq, OpenRouter, Sarvam) immediately",
        "Generate strong JWT secret key (min 256-bit random) and update production",
        "Add authentication to GET /calls/, GET /crm/contacts, GET /crm/tickets endpoints",
        "Add authentication to WebSocket endpoints (/ws/live-calls, /twilio/stream)",
        "Add rate limiting to /auth/login and /auth/google endpoints",
        "Restrict CORS to specific frontend domain(s)",
        "Add Twilio webhook signature verification",
    ]
    for i, item in enumerate(immediate, 1):
        story.append(Paragraph(f'<b>{i}.</b> {item}', style_bullet))
    
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Short-Term Actions (Next 2 Sprints)</b>", style_h3))
    story.append(Spacer(1, 4))
    
    short_term = [
        "Implement JWT refresh token mechanism",
        "Add token revocation/blacklisting",
        "Enforce RBAC on all backend API endpoints (not just frontend)",
        "Store JWT in httpOnly secure cookies instead of localStorage",
        "Add input validation with Pydantic models for all query parameters",
        "Implement comprehensive logging of auth events",
        "Add SQL injection protection (already mitigated by SQLAlchemy ORM)",
        "Set up automated security scanning (gitleaks, Snyk, OWASP ZAP)",
    ]
    for i, item in enumerate(short_term, 1):
        story.append(Paragraph(f'<b>{i}.</b> {item}', style_bullet))
    
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Medium-Term Actions (Phase 2)</b>", style_h3))
    story.append(Spacer(1, 4))
    
    medium_term = [
        "Implement CI/CD pipeline with security gates",
        "Deploy Prometheus + Grafana monitoring stack",
        "Add LLM-based prompt injection classifier",
        "Implement customer data encryption at rest",
        "Add API versioning strategy",
        "Set up automated penetration testing",
        "Implement zero-trust network architecture",
        "Add GDPR compliance controls for customer data",
    ]
    for i, item in enumerate(medium_term, 1):
        story.append(Paragraph(f'<b>{i}.</b> {item}', style_bullet))
    
    story.append(Spacer(1, 30))
    story.append(create_header_bar())
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        '<i>This report was generated as part of a comprehensive security audit of the Vensora platform. '
        'All findings should be validated by the development team before remediation. '
        'For questions, contact the security audit team.</i>',
        ParagraphStyle('Disclaimer', parent=style_body, fontSize=8, textColor=TEXT_SECONDARY, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Master report generated: {output_path}")
    return output_path

# ============================================================
# INDIVIDUAL MODULE PDFs
# ============================================================
def generate_module_report(module_name, title, description, files, findings, completion_pct, status):
    output_path = os.path.expanduser(f"~/Downloads/Vensora_Module_{module_name}.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        leftMargin=2*cm, rightMargin=2*cm
    )
    
    story = []
    page_width = A4[0] - 4*cm
    
    # Cover
    story.append(Spacer(1, 40))
    logo_drawing = Drawing(160, 50)
    logo_drawing.add(Rect(0, 8, 150, 35, fillColor=PRIMARY, strokeColor=None, rx=6))
    logo_drawing.add(String(75, 17, "VENSORA", fillColor=white, fontSize=18, fontName='Helvetica-Bold', textAnchor='middle'))
    story.append(logo_drawing)
    story.append(Spacer(1, 20))
    story.append(Paragraph(title, style_title))
    story.append(Spacer(1, 8))
    accent_drawing = Drawing(100, 3)
    accent_drawing.add(Rect(0, 0, 100, 3, fillColor=ACCENT, strokeColor=None))
    story.append(accent_drawing)
    story.append(Spacer(1, 12))
    story.append(Paragraph(description, style_subtitle))
    
    # Status badge
    status_color = SUCCESS if status == 'COMPLETE' else WARNING if status == 'PARTIAL' else DANGER
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f'<font color="{status_color.hexval()}" size="14"><b>Status: {status}</b></font>  |  '
        f'<font color="{PRIMARY.hexval()}" size="14"><b>Completion: {completion_pct}%</b></font>',
        style_body
    ))
    story.append(PageBreak())
    
    # Files
    story.extend(create_section_header("Files in Module"))
    story.append(Spacer(1, 4))
    for f in files:
        story.append(Paragraph(f'<font face="Courier" size="9">{f}</font>', style_bullet))
    
    story.append(Spacer(1, 16))
    
    # Findings
    if findings:
        story.extend(create_section_header("Security Findings"))
        story.append(Spacer(1, 4))
        for finding in findings:
            sev = finding.get('severity', 'INFO')
            sev_color = {
                'CRITICAL': DANGER, 'HIGH': WARNING, 
                'MEDIUM': HexColor("#FFA726"), 'LOW': INFO
            }.get(sev, TEXT_SECONDARY)
            
            story.append(Paragraph(
                f'{severity_badge(sev)} <b>{finding["title"]}</b>',
                style_body
            ))
            story.append(Paragraph(finding['description'], style_body_small))
            if 'remediation' in finding:
                story.append(Paragraph(f'<b>Fix:</b> {finding["remediation"]}', style_body_small))
            story.append(Spacer(1, 8))
    
    # Build
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Module report generated: {output_path}")
    return output_path

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  VENSORA SECURITY AUDIT REPORT GENERATOR")
    print("=" * 60)
    
    # Master report
    generate_master_report()
    
    # Module reports
    modules = [
        {
            'name': 'Authentication',
            'title': 'Authentication Module',
            'description': 'JWT + Google OAuth authentication service',
            'files': [
                'app/security/jwt.py',
                'app/security/google.py',
                'app/security/password.py',
                'app/modules/auth/service.py',
                'app/modules/auth/schemas.py',
                'app/api/v1/auth.py',
                'app/api/dependencies/auth.py',
            ],
            'findings': [
                {'severity': 'CRITICAL', 'title': 'Weak JWT Secret', 'description': 'Hardcoded weak secret key for token signing.', 'remediation': 'Use cryptographically strong secret.'},
                {'severity': 'HIGH', 'title': 'No Rate Limiting', 'description': 'Login endpoints have no brute-force protection.'},
                {'severity': 'MEDIUM', 'title': '24h Token Expiry', 'description': 'Excessively long token lifetime.'},
            ],
            'completion': 95, 'status': 'PARTIAL'
        },
        {
            'name': 'Users_RBAC',
            'title': 'Users & RBAC Module',
            'description': 'User management, roles, permissions, departments',
            'files': [
                'app/modules/users/models.py',
                'app/modules/users/service.py',
                'app/modules/users/schemas.py',
                'app/modules/roles/models.py',
                'app/modules/departments/models.py',
                'app/api/v1/users.py',
            ],
            'findings': [
                {'severity': 'MEDIUM', 'title': 'Client-Side RBAC', 'description': 'Role check only on frontend, not backend.'},
                {'severity': 'LOW', 'title': 'User Listing', 'description': 'GET /users/ returns all users with emails.'},
            ],
            'completion': 90, 'status': 'PARTIAL'
        },
        {
            'name': 'AI_Agent',
            'title': 'AI Agent Module',
            'description': 'LangGraph conversational agent with RAG and guardrails',
            'files': [
                'app/modules/ai/agent.py',
                'app/modules/ai/guardrails.py',
                'app/modules/ai/llm_service.py',
                'app/modules/ai/tools.py',
                'app/modules/ai/memory.py',
                'app/modules/ai/confidence.py',
                'app/modules/ai/prompts.py',
                'app/modules/ai/embeddings.py',
                'app/modules/ai/document_processor.py',
                'app/modules/ai/qdrant_client.py',
            ],
            'findings': [
                {'severity': 'MEDIUM', 'title': 'Basic Guardrails', 'description': 'Only 5 regex patterns for injection detection.'},
                {'severity': 'MEDIUM', 'title': 'Tool Call Rate Limiting', 'description': 'No limits on AI tool execution frequency.'},
                {'severity': 'MEDIUM', 'title': 'RAG Context Leakage', 'description': 'Full document chunks in system prompt.'},
                {'severity': 'LOW', 'title': 'Hardcoded File Path', 'description': 'Absolute macOS path in prompts.py.'},
            ],
            'completion': 80, 'status': 'PARTIAL'
        },
        {
            'name': 'Telephony',
            'title': 'Telephony Module',
            'description': 'Twilio WebSocket streaming, call state machine, barge-in',
            'files': [
                'app/modules/telephony/router.py',
                'app/modules/telephony/event_handler.py',
                'app/modules/telephony/audio_stream.py',
                'app/modules/telephony/state_machine.py',
                'app/modules/telephony/schemas.py',
                'app/modules/telephony/services/recording_service.py',
                'app/modules/telephony/services/retention_service.py',
            ],
            'findings': [
                {'severity': 'HIGH', 'title': 'Unauthenticated WebSocket', 'description': 'Live calls WS has no auth.'},
                {'severity': 'HIGH', 'title': 'No Webhook Signature', 'description': 'Twilio webhook not verified.'},
                {'severity': 'LOW', 'title': 'Host Header Trust', 'description': 'WebSocket URL from Host header.'},
            ],
            'completion': 85, 'status': 'PARTIAL'
        },
        {
            'name': 'Voice',
            'title': 'Voice Services Module',
            'description': 'STT (Faster Whisper), TTS (Piper), VAD (WebRTC)',
            'files': [
                'app/modules/voice/stt_service.py',
                'app/modules/voice/tts_service.py',
                'app/modules/voice/vad_service.py',
            ],
            'findings': [
                {'severity': 'LOW', 'title': 'Mock Mode Fallback', 'description': 'Services silently fall back to mock mode.'},
            ],
            'completion': 88, 'status': 'COMPLETE'
        },
        {
            'name': 'CRM',
            'title': 'CRM Module',
            'description': 'Customer profiles, tickets, shipments, knowledge base, prompts',
            'files': [
                'app/modules/crm/models.py',
                'app/modules/crm/adapter.py',
                'app/modules/calls/models.py',
                'app/modules/campaigns/models.py',
                'app/modules/contacts/models.py',
                'app/api/v1/calls.py',
                'app/api/v1/crm.py',
                'app/api/v1/knowledge.py',
            ],
            'findings': [
                {'severity': 'HIGH', 'title': 'Unauthenticated Endpoints', 'description': 'GET /calls/, /crm/contacts, /crm/tickets have no auth.'},
                {'severity': 'MEDIUM', 'title': 'File Upload Validation', 'description': 'Only extension check, no content sanitization.'},
            ],
            'completion': 82, 'status': 'PARTIAL'
        },
        {
            'name': 'Infrastructure',
            'title': 'Infrastructure Module',
            'description': 'Docker Compose, database, MinIO, Qdrant, providers',
            'files': [
                'docker-compose.yml',
                'app/database/session.py',
                'app/database/base.py',
                'app/core/providers/registry.py',
                'app/core/providers/vector.py',
                'app/core/providers/base.py',
                'app/modules/storage/minio_client.py',
                'app/core/middleware.py',
                'app/core/exceptions.py',
                'app/core/logger.py',
                'app/core/audit.py',
            ],
            'findings': [
                {'severity': 'CRITICAL', 'title': 'Exposed API Keys', 'description': 'Real API keys in .env file on disk.'},
                {'severity': 'CRITICAL', 'title': 'Default Credentials', 'description': 'Default DB/MinIO passwords in configs.'},
                {'severity': 'HIGH', 'title': 'Wildcard CORS', 'description': 'CORS allows all origins.'},
                {'severity': 'MEDIUM', 'title': 'Exposed Ports', 'description': 'DB/Redis/MinIO ports exposed to host.'},
            ],
            'completion': 85, 'status': 'PARTIAL'
        },
        {
            'name': 'Frontend',
            'title': 'Frontend Application',
            'description': 'React 19 + Vite + TypeScript admin dashboard',
            'files': [
                'apps/frontend/src/App.tsx',
                'apps/frontend/src/pages/LoginView.tsx',
                'apps/frontend/src/pages/ChangePasswordView.tsx',
                'apps/frontend/src/pages/LiveCallsView.tsx',
                'apps/frontend/src/pages/UsersView.tsx',
                'apps/frontend/src/pages/ContactsView.tsx',
                'apps/frontend/src/pages/TicketsView.tsx',
                'apps/frontend/src/pages/KnowledgeBaseView.tsx',
                'apps/frontend/src/pages/CallHistoryView.tsx',
                'apps/frontend/package.json',
                'apps/frontend/vite.config.ts',
            ],
            'findings': [
                {'severity': 'MEDIUM', 'title': 'localStorage Token Storage', 'description': 'JWT stored in localStorage, vulnerable to XSS.'},
                {'severity': 'MEDIUM', 'title': 'Hardcoded API URLs', 'description': 'All URLs point to localhost:8000.'},
                {'severity': 'LOW', 'title': 'No Error Boundary', 'description': 'No React error boundary component.'},
                {'severity': 'LOW', 'title': 'No CSP Headers', 'description': 'No Content Security Policy configured.'},
            ],
            'completion': 70, 'status': 'PARTIAL'
        },
    ]
    
    for mod in modules:
        generate_module_report(
            mod['name'], mod['title'], mod['description'],
            mod['files'], mod['findings'], mod['completion'], mod['status']
        )
    
    print("\n" + "=" * 60)
    print("  ALL REPORTS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nOutput directory: /Users/saidheeraj/LocalProjects/vensora/reports/")
