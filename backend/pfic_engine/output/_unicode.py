"""Unicode helpers for reportlab PDF generation."""
import unicodedata

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Register a CID font for CJK and other non-latin-1 text.
# STSong-Light is built into reportlab (no font file needed); PDF viewers
# substitute an appropriate system font when rendering.
_CJK_FONT: str | None = None
for _candidate in ("STSong-Light", "HeiseiMin-W3", "HYSMyeongJo-Medium"):
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_candidate))
        _CJK_FONT = _candidate
        break
    except Exception:
        pass


def u(text: str) -> str:
    """Return text safe for a reportlab Paragraph.

    Pure latin-1 text is returned unchanged.  Text containing other characters
    is XML-escaped then wrapped in a <font> tag that switches to the registered
    CID font.  Falls back to latin-1 replacement chars if no CID font loaded.
    """
    s = str(text) if text is not None else ""
    try:
        s.encode("latin-1")
        return s
    except (UnicodeEncodeError, UnicodeDecodeError):
        s_esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if _CJK_FONT:
            return f'<font name="{_CJK_FONT}">{s_esc}</font>'
        return s.encode("latin-1", errors="replace").decode("latin-1")


def safe_filename(text: str) -> str:
    """Return an ASCII-safe filename component (for Content-Disposition headers)."""
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in ascii_text)
    return safe or "export"
