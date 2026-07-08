import zipfile

docx_path = "scripts/templates/Completion_Certificate.docx"
with zipfile.ZipFile(docx_path, "r") as z:
    media_files = [f for f in z.namelist() if "word/media/" in f]
    print("Media files in DOCX template:")
    for f in media_files:
        print(f"  - {f} (size: {z.getinfo(f).file_size} bytes)")
