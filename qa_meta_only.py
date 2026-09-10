from pathlib import Path
import re

ROOT = Path("website")
files = [
    "index.html",
    "about.html",
    "courses.html",
    "contact.html",
    "medical-coding-classes-in-kolhapur.html",
    "medical-coding-classes-in-sangli.html",
    "medical-coding-classes-in-satara.html",
    "medical-coding-classes-in-belgaum.html",
]
want = {
    "index.html": (58, 155),
    "about.html": (52, 156),
    "courses.html": (54, 150),
    "contact.html": (50, 147),
    "medical-coding-classes-in-kolhapur.html": (51, 155),
    "medical-coding-classes-in-sangli.html": (50, 158),
    "medical-coding-classes-in-satara.html": (50, 154),
    "medical-coding-classes-in-belgaum.html": (54, 158),
}
all_ok = True
for f in files:
    html = (ROOT / f).read_text(encoding="utf-8")
    t = re.search(r"<title>(.*?)</title>", html, re.I | re.S).group(1).strip()
    d = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I).group(1).strip()
    tl, dl = want[f]
    ok = len(t) == tl and len(d) == dl
    all_ok &= ok
    print(f"{'OK' if ok else 'FAIL'} {f}: title {len(t)}/{tl}, desc {len(d)}/{dl}")
print("ALL META OK" if all_ok else "META FAIL")
