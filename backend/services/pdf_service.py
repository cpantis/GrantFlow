"""PDF Generation Service - Creates PDF documents from AI-generated content"""
import os
import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor
import re

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated")


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='DocTitle', fontSize=16, leading=20, alignment=TA_CENTER,
        spaceAfter=20, fontName='Helvetica-Bold', textColor=HexColor('#1a1a2e')
    ))
    styles.add(ParagraphStyle(
        name='DocSubtitle', fontSize=11, leading=14, alignment=TA_CENTER,
        spaceAfter=30, textColor=HexColor('#6b7280')
    ))
    styles.add(ParagraphStyle(
        name='SectionH2', fontSize=13, leading=16, spaceBefore=16, spaceAfter=8,
        fontName='Helvetica-Bold', textColor=HexColor('#1e3a5f'),
        borderWidth=0, leftIndent=0
    ))
    styles.add(ParagraphStyle(
        name='SectionH3', fontSize=11, leading=14, spaceBefore=12, spaceAfter=6,
        fontName='Helvetica-Bold', textColor=HexColor('#2563eb')
    ))
    styles.add(ParagraphStyle(
        name='BodyText2', fontSize=10, leading=14, alignment=TA_JUSTIFY,
        spaceAfter=6, textColor=HexColor('#374151')
    ))
    styles.add(ParagraphStyle(
        name='BulletItem', fontSize=10, leading=14, leftIndent=20,
        spaceAfter=3, textColor=HexColor('#374151'), bulletIndent=8
    ))
    styles.add(ParagraphStyle(
        name='BlockQuote', fontSize=10, leading=14, leftIndent=20,
        spaceAfter=8, textColor=HexColor('#6b7280'), fontName='Helvetica-Oblique',
        borderWidth=1, borderColor=HexColor('#2563eb'), borderPadding=6
    ))
    styles.add(ParagraphStyle(
        name='Footer', fontSize=8, leading=10, alignment=TA_CENTER,
        textColor=HexColor('#9ca3af')
    ))
    return styles


def _markdown_to_flowables(text: str, styles) -> list:
    """Convert markdown text to ReportLab flowables."""
    flowables = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        if line.startswith('## '):
            content = line[3:].strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            flowables.append(Paragraph(content, styles['SectionH2']))
            i += 1
            continue

        if line.startswith('### '):
            content = line[4:].strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            flowables.append(Paragraph(content, styles['SectionH3']))
            i += 1
            continue

        if line.startswith('# '):
            content = line[2:].strip()
            flowables.append(Paragraph(content, styles['DocTitle']))
            i += 1
            continue

        # Blockquote
        if line.startswith('> '):
            content = line[2:].strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            flowables.append(Paragraph(content, styles['BlockQuote']))
            i += 1
            continue

        # Bullet list
        if line.startswith('- ') or line.startswith('* '):
            content = line[2:].strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            content = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', content)
            flowables.append(Paragraph(f'• {content}', styles['BulletItem']))
            i += 1
            continue

        # Numbered list
        m = re.match(r'^(\d+)\.\s+(.*)', line)
        if m:
            num = m.group(1)
            content = m.group(2).strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            flowables.append(Paragraph(f'{num}. {content}', styles['BulletItem']))
            i += 1
            continue

        # Horizontal rule
        if line.startswith('---'):
            flowables.append(Spacer(1, 8))
            i += 1
            continue

        # Regular paragraph
        content = line
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
        content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)
        content = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', content)
        flowables.append(Paragraph(content, styles['BodyText2']))
        i += 1

    return flowables


def generate_pdf(title: str, content: str, firm_name: str = "", project_name: str = "") -> str:
    """Generate a PDF from markdown content. Returns the file path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    import uuid
    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(UPLOAD_DIR, filename)

    styles = _get_styles()

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm
    )

    flowables = []

    # Header
    flowables.append(Paragraph(title, styles['DocTitle']))
    if firm_name or project_name:
        sub = []
        if firm_name:
            sub.append(firm_name)
        if project_name:
            sub.append(f'Proiect: {project_name}')
        flowables.append(Paragraph(' | '.join(sub), styles['DocSubtitle']))

    flowables.append(Spacer(1, 12))

    # Content
    flowables.extend(_markdown_to_flowables(content, styles))

    # Footer
    flowables.append(Spacer(1, 30))
    from datetime import datetime, timezone
    flowables.append(Paragraph(
        f'Generat de GrantFlow | {datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")} UTC',
        styles['Footer']
    ))

    doc.build(flowables)
    logger.info(f"PDF generated: {filepath}")
    return filename
