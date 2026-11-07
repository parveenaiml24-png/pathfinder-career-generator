from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def career_profile_pdf(payload, student_name):
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, title="Career Profile")
    styles = getSampleStyleSheet()
    story = [Paragraph(f"{student_name} — Career Profile", styles["Title"]), Spacer(1, 16)]
    sections = [
        ("Professional summary", payload.get("professional_summary", "")),
        ("Career objective", payload.get("career_objective", "")),
        ("LinkedIn About", payload.get("linkedin_about", "")),
        ("Portfolio introduction", payload.get("portfolio_intro", "")),
        ("Interview introduction", payload.get("interview_intro", "")),
        ("Recommended roles", ", ".join(payload.get("roles", []))),
        ("Strengths", ", ".join(payload.get("strengths", []))),
        ("Areas to develop", ", ".join(payload.get("improvements", []))),
    ]
    for heading, text in sections:
        story.extend([Paragraph(heading, styles["Heading2"]), Paragraph(text, styles["BodyText"]), Spacer(1, 9)])
    document.build(story)
    buffer.seek(0)
    return buffer
