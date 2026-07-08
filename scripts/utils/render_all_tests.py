import fitz
import os

pdf_names = ["test_qr_output", "test_qr_in_textbox", "test_qr_p0"]

os.makedirs("scripts/output/rendered", exist_ok=True)
for name in pdf_names:
    pdf_path = f"scripts/output/{name}.pdf"
    if os.path.exists(pdf_path):
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap()
        output_png = f"scripts/output/rendered/{name}.png"
        pix.save(output_png)
        print(f"Saved {pdf_path} page 1 to {output_png}")
