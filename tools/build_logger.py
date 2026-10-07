"""Build web/logger.html: the Incident Logger page, with its core and two libraries inlined.

Run from the repo root:  python tools/build_logger.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


def _safe(js: str) -> str:
    """Make library source safe to place inside an inline <script> block."""
    return js.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def render() -> str:
    page = (WEB / "logger.template.html").read_text(encoding="utf-8")
    core = (WEB / "logger.core.js").read_text(encoding="utf-8")
    xlsx = (WEB / "vendor" / "xlsx.full.min.js").read_text(encoding="utf-8")
    pdf = (WEB / "vendor" / "jspdf.umd.min.js").read_text(encoding="utf-8")
    for marker in ("__CORE__", "__XLSX__", "__JSPDF__"):
        assert page.count(marker) == 1, marker
    return page.replace("__CORE__", _safe(core)).replace("__XLSX__", _safe(xlsx)).replace("__JSPDF__", _safe(pdf))


def main() -> None:
    out = WEB / "logger.html"
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
