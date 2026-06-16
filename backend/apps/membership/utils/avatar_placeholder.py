import io

from PIL import Image as PILImage, ImageDraw


def avatar_placeholder_png(size: int = 128) -> io.BytesIO:
    """Silhueta de perfil (mesmo visual do frontend) para PDFs e fallback."""
    gold = (232, 213, 168)
    burgundy = (92, 40, 48)
    img = PILImage.new("RGB", (size, size), color=gold)
    draw = ImageDraw.Draw(img)

    head_r = int(size * 0.156)
    head_cx, head_cy = size // 2, int(size * 0.36)
    draw.ellipse(
        (head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r),
        fill=burgundy,
    )
    draw.ellipse(
        (int(size * 0.19), int(size * 0.52), int(size * 0.81), int(size * 1.02)),
        fill=burgundy,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
