from docx import Document

doc = Document("scripts/templates/Completion_Certificate.docx")
namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# Find all paragraphs in the document (including those in textboxes)
p_elements = doc.element.body.xpath("//w:p")
print(f"Total paragraphs found: {len(p_elements)}")

for i, p_elem in enumerate(p_elements):
    # Get all text nodes in this paragraph
    text = "".join(node.text for node in p_elem.xpath(".//w:t"))
    # Check if this paragraph is inside a textbox
    is_textbox = len(p_elem.xpath("ancestor::w:txbxContent")) > 0
    print(f"P{i} (in_textbox={is_textbox}): '{text}'")
