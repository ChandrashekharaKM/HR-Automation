import fitz

for path in ["scripts/output/test_qr_output.pdf", "scripts/output/test_qr_in_textbox.pdf", "scripts/output/test_qr_p0.pdf"]:
    try:
        doc = fitz.open(path)
        print(f"{path}: actual page count = {len(doc)}")
    except Exception as e:
        print(f"Failed to open {path}: {e}")
