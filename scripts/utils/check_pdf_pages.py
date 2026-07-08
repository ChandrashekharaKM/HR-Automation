import re

pdf_path = "scripts/output/test_qr_output.pdf"
with open(pdf_path, "rb") as f:
    content = f.read()

# Count occurrences of '/Type /Page' (standard PDF page object indicator)
pages = len(re.findall(b"/Type\s*/Page", content))
print("Number of pages in PDF:", pages)
