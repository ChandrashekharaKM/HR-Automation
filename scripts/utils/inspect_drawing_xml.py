from docx import Document

doc = Document("scripts/templates/Completion_Certificate.docx")
p0 = doc.paragraphs[0]

namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
drawings = p0._element.xpath(".//w:drawing")
print(f"Total drawing elements: {len(drawings)}")

for idx, draw in enumerate(drawings):
    text = "".join(node.text for node in draw.xpath(".//w:t", namespaces=namespaces))
    if "{CURRENT_DATE}" in text:
        import lxml.etree as etree
        print(f"\n--- Drawing {idx} containing {{CURRENT_DATE}} ---")
        print(etree.tostring(draw, pretty_print=True, encoding="utf-8").decode("utf-8")[:2000])
        break
