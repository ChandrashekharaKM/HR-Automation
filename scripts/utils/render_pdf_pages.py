import fitz # PyMuPDF
import os

pdf_path = "scripts/output/test_qr_in_textbox.pdf"
doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

os.makedirs("scripts/output/rendered", exist_ok=True)
for i in range(len(doc)):
    page = doc.load_page(i)
    pix = page.get_pixmap()
    output_png = f"scripts/output/rendered/page_{i+1}.png"
    pix.save(output_png)
    print(f"Saved page {i+1} to {output_png} (size: {pix.width}x{pix.height})")
