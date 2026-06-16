"""OCR do calendário paroquial (PDF escaneado) para texto."""
import sys
from pathlib import Path

import easyocr
import fitz
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "calendario_ocr.txt"


def render_page(page, scale: float = 2.0) -> np.ndarray:
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)


def main() -> None:
    pdfs = list(ROOT.glob("*.pdf"))
    if not pdfs:
        print("Nenhum PDF na raiz", file=sys.stderr)
        sys.exit(1)

    pdf_path = pdfs[0]
    doc = fitz.open(pdf_path)
    reader = easyocr.Reader(["pt"], gpu=False, verbose=False)

    lines = [f"FILE: {pdf_path.name}", f"PAGES: {doc.page_count}", ""]
    for i in range(doc.page_count):
        img = render_page(doc[i])
        chunks = reader.readtext(img, detail=0, paragraph=True)
        lines.append(f"=== PAGE {i + 1} ===")
        lines.extend(chunks)
        lines.append("")
        print(f"OCR page {i + 1}/{doc.page_count}", flush=True)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
