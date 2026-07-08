from docx import Document

doc = Document("scripts/templates/Completion_Certificate.docx")
p0 = doc.paragraphs[0]
namespaces = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
}

drawings = p0._element.xpath(".//w:drawing")
print(f"Total drawings: {len(drawings)}")

for idx, draw in enumerate(drawings):
    text = "".join(node.text for node in draw.xpath(".//w:t", namespaces=namespaces))
    
    # Get positions if present
    h_pos = draw.xpath(".//wp:positionH/wp:posOffset", namespaces=namespaces)
    v_pos = draw.xpath(".//wp:positionV/wp:posOffset", namespaces=namespaces)
    extent = draw.xpath(".//wp:extent", namespaces=namespaces)
    
    h_val = int(h_pos[0].text) / 914400 if h_pos else None
    v_val = int(v_pos[0].text) / 914400 if v_pos else None
    w_val = int(extent[0].get("cx")) / 914400 if extent else None
    h_size = int(extent[0].get("cy")) / 914400 if extent else None
    
    doc_pr = draw.xpath(".//wp:docPr", namespaces=namespaces)
    name = doc_pr[0].get("name") if doc_pr else "Unknown"
    
    print(f"\nDrawing {idx}: '{name}'")
    print(f"  Text contained: '{text[:100]}'")
    print(f"  Position: H = {h_val:.3f} in, V = {v_val:.3f} in" if h_val is not None else "  Position: Inline")
    print(f"  Size: Width = {w_val:.3f} in, Height = {h_size:.3f} in" if w_val is not None else "  Size: Unknown")
