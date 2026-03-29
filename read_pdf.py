import pdfplumber

path = r"c:\Users\DELL\Desktop\ld2450-tinyml\intrim-1 template.pdf (1) (1).pdf"

with pdfplumber.open(path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"  PAGE {i+1}")
        print(f"{'='*60}")
        text = page.extract_text()
        if text:
            print(text)
        else:
            print("(no extractable text on this page)")
