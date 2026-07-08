from docx import Document
from docx.shared import Inches

doc = Document("scripts/templates/Completion_Certificate.docx")
section = doc.sections[0]

print("Page Width:", section.page_width.inches)
print("Page Height:", section.page_height.inches)
print("Top Margin:", section.top_margin.inches)
print("Bottom Margin:", section.bottom_margin.inches)
print("Left Margin:", section.left_margin.inches)
print("Right Margin:", section.right_margin.inches)
