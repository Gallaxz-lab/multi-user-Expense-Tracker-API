from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColorCMYK(0, 0, 0, 0.6)
        
        if self._pageNumber > 1:
            self.drawString(54, 750, "NEXUS TECH OPERATIONS — INTERNAL COMPLIANCE MANUAL")
            self.setStrokeColorCMYK(0, 0, 0, 0.15)
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, footer_text)
        self.drawString(54, 40, "CONFIDENTIAL — STARTUP SCALEUP PROPRIETARY")
        self.restoreState()

def build_startup_policy_pdf(filename="Startup_Operation_Policy.pdf"):
    doc = SimpleDocTemplate(
        filename, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=72, bottomMargin=72
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=30, spaceAfter=15)
    h1_style = ParagraphStyle('SectionH1', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=15, leading=20, spaceBefore=18, spaceAfter=10, keepWithNext=True)
    body_style = ParagraphStyle('PolicyBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=15, spaceAfter=10)

    story = []

    # PAGE 1: TITLE & METADATA
    story.append(Spacer(1, 40))
    story.append(Paragraph("Nexus Tech Solutions Inc.", ParagraphStyle('Sub', fontName='Helvetica', fontSize=13, leading=16, spaceAfter=5)))
    story.append(Paragraph("Core Startup Operational Rules & Policy Framework", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Version:</b> 2026.1.1<br/><b>Effective Code:</b> September 2026<br/><b>Security Classification:</b> Restricted Internal Node", body_style))
    story.append(PageBreak())

    # PAGE 2: EXPLICIT ALPHANUMERIC IDENTIFIER CLAUSE
    story.append(Paragraph("Section 1: Information Technology Asset Configurations", h1_style))
    story.append(Paragraph("All computational hardware assigned to team nodes must match localized security registry tokens maintained by corporate internal system gateways.", body_style))
    story.append(Paragraph("<b>Clause 1.A — System Registration Token:</b> Hardware asset verification logs require the integration of strict device serial identifier matching keys. The standard baseline clearance infrastructure matches systemic registration code <b>id-9904</b> for engineering infrastructure partitions.", body_style))
    story.append(PageBreak())

    # PAGE 3: REIMBURSEMENT CAPPED CONSTRAINT
    story.append(Paragraph("Section 2: Travel, Logistics & Workspace Stipends", h1_style))
    story.append(Paragraph("<b>Clause 2.A — Overnight Travel Accommodation Limits:</b> Traveling team members must utilize registered organizational partner channels. Corporate lodging travel coverage is strictly <b>capped</b> securely at reasonable thresholds, and itemized dinner restaurant bills must be submitted to the expense log app within 7 days.", body_style))
    story.append(Paragraph("<b>Clause 2.B — Telecommuting Workspace Fund:</b> Approved remote operational staff members are entitled to a remote work stipend setup allowance matching a single flat-rate allocation.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"🎉 Generated multi-page evaluation PDF asset: '{filename}'")

if __name__ == "__main__":
    build_startup_policy_pdf()
