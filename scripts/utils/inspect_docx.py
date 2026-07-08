from docx import Document

doc = Document("scripts/templates/Completion_Certificate.docx")
body = doc.element.body
namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
text_elements = body.xpath("//w:t")
print(f"Total w:t elements: {len(text_elements)}")
for idx, t in enumerate(text_elements):
    parent_p = t.xpath("ancestor::w:p[1]")
    parent_p_tag = parent_p[0].tag if parent_p else "None"
    is_textbox = len(t.xpath("ancestor::w:txbxContent")) > 0
    if "{" in t.text or "}" in t.text or idx < 20:
        print(f"{idx}: text=\"{t.text}\", parent_p={parent_p_tag}, is_textbox={is_textbox}")
