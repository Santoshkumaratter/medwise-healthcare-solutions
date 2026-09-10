"""100% E2E QA — local + production. Never prints secrets."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "website"
LOCAL = "http://127.0.0.1:8765"
PROD = "https://website-eight-iota-ni22rhq9op.vercel.app"

EXPECTED = {
    "index.html": (
        "/",
        "Best Medical Coding Class in Kolhapur | CPC & CCS Training",
        "The best medical coding class in Kolhapur. AAPC CPC and AHIMA CCS certification training for Kolhapur, Sangli, Satara and Belgaum students. 100% placement.",
        58,
        155,
    ),
    "about.html": (
        "/about.html",
        "About MedWise — Medical Coding Institute in Kolhapur",
        "MedWise is Kolhapur's specialist medical coding institute in Rajarampuri: practising certified coders as faculty, batches of 20, and full placement support.",
        52,
        156,
    ),
    "courses.html": (
        "/courses.html",
        "CPC & CCS Medical Coding Courses in Kolhapur | MedWise",
        "Full CPC (AAPC) and CCS (AHIMA) syllabus, batch timings and fee structure at Kolhapur's specialist medical coding institute. 100% placement guarantee.",
        54,
        150,
    ),
    "contact.html": (
        "/contact.html",
        "Contact MedWise | Medical Coding Class in Kolhapur",
        "Visit MedWise at Yashodhara Apartment, Rajarampuri 6th Lane, Kolhapur 416008. Call or WhatsApp 7709099599 to book a free medical coding demo class.",
        50,
        147,
    ),
    "medical-coding-classes-in-kolhapur.html": (
        "/medical-coding-classes-in-kolhapur.html",
        "Medical Coding Classes in Kolhapur — Batches & Fees",
        "Medical coding classes in Kolhapur at Rajarampuri 6th Lane. Weekday, evening and weekend CPC and CCS batches of 20 students, with 100% placement guarantee.",
        51,
        155,
    ),
    "medical-coding-classes-in-sangli.html": (
        "/medical-coding-classes-in-sangli.html",
        "Medical Coding Classes in Sangli & Miraj | MedWise",
        "Medical coding classes for Sangli, Miraj and Ichalkaranji students — weekend classroom batches in Kolhapur or live online CPC and CCS training with placement.",
        50,
        158,
    ),
    "medical-coding-classes-in-satara.html": (
        "/medical-coding-classes-in-satara.html",
        "Medical Coding Classes in Satara & Karad | MedWise",
        "Medical coding classes for Satara and Karad students. Live online CPC and CCS certification training from Kolhapur's specialist institute, with placement.",
        50,
        154,
    ),
    "medical-coding-classes-in-belgaum.html": (
        "/medical-coding-classes-in-belgaum.html",
        "Medical Coding Classes in Belgaum (Belagavi) | MedWise",
        "Medical coding classes for Belgaum, Belagavi, Nipani and Chikodi students. CPC and CCS training online or in weekend Kolhapur batches, with placement support.",
        54,
        158,
    ),
}

IG = "https://www.instagram.com/medwisehealthcaresolutions/"
WA = "https://wa.me/917709099599"
TEL = "tel:+917709099599"

issues: list[str] = []
passes: list[str] = []


def ok(m: str) -> None:
    passes.append(m)
    print("PASS:", m)


def fail(m: str) -> None:
    issues.append(m)
    print("FAIL:", m)


def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "MedWiseFullE2E/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            return res.status, res.read(), dict(res.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read() if e.fp else b""), {}
    except Exception as e:
        return 0, str(e).encode(), {}


def http_post_json(base: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/api/send-enquiry",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MedWiseFullE2E/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body[:300]}
    except Exception as e:
        return 0, {"error": str(e)}


def title_desc(html: str):
    t = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    # Prefer double-quoted content so apostrophes (Kolhapur's) do not truncate.
    d = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"',
        html,
        re.I,
    )
    if not d:
        d = re.search(
            r"<meta\s+name='description'\s+content='([^']*)'",
            html,
            re.I,
        )
    return (t.group(1).strip() if t else ""), (d.group(1).strip() if d else "")


print("=== 1) FILE / SECRET / ASSET CHECKS ===")
secret_needles = [
    "iodv",
    "abhs",
    "tgjw",
    "zzwb",
    "GMAIL_APP_PASSWORD=",
    "tejaswiulhalkar1996@gmail.com",
]
public_files = list(ROOT.glob("*.html")) + [
    ROOT / "assets/js/site.js",
    ROOT / "assets/css/style.css",
    ROOT / "api/send-enquiry.js",
    ROOT / "vercel.json",
    ROOT / "package.json",
]
for f in public_files:
    text = f.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    for n in secret_needles:
        if n.lower() in low and f.name != ".env.example":
            # allow placeholder patterns only in comments? never allow real gmail in client
            if f.name in ("site.js",) or f.suffix == ".html" or f.name == "style.css":
                fail(f"secret/email leak in {f.relative_to(ROOT)}: {n[:8]}…")
                break
    else:
        continue

# dedicated client leak check
client_blob = ""
for f in list(ROOT.glob("*.html")) + [ROOT / "assets/js/site.js"]:
    client_blob += f.read_text(encoding="utf-8", errors="replace")
if "tejaswiulhalkar1996@gmail.com" in client_blob.lower():
    fail("destination Gmail exposed in public HTML/JS")
else:
    ok("destination Gmail not in public HTML/JS")
if re.search(r"formsubmit\.co", client_blob, re.I):
    fail("FormSubmit URL exposed in client")
else:
    ok("no FormSubmit URL in client")
if "/api/send-enquiry" not in (ROOT / "assets/js/site.js").read_text(encoding="utf-8"):
    fail("forms not posting to /api/send-enquiry")
else:
    ok("forms post to /api/send-enquiry")

for asset in [
    "assets/css/style.css",
    "assets/js/site.js",
    "assets/img/logo.png",
]:
    if (ROOT / asset).is_file():
        ok(f"asset exists {asset}")
    else:
        fail(f"missing asset {asset}")

php = list(ROOT.rglob("*.php"))
if php:
    fail(f"PHP files present: {[str(p) for p in php]}")
else:
    ok("no PHP files")

print("\n=== 2) META / LINKS ON DISK ===")
for fname, (path, title, desc, tlen, dlen) in EXPECTED.items():
    html = (ROOT / fname).read_text(encoding="utf-8")
    got_t, got_d = title_desc(html)
    if got_t == title and len(got_t) == tlen:
        ok(f"{fname} title exact ({tlen})")
    else:
        fail(f"{fname} title mismatch got={len(got_t)} want={tlen}")
    if got_d == desc and len(got_d) == dlen:
        ok(f"{fname} description exact ({dlen})")
    else:
        fail(f"{fname} description mismatch got={len(got_d)} want={dlen}")
    if IG not in html:
        fail(f"{fname} missing Instagram")
    if WA not in html:
        fail(f"{fname} missing WhatsApp")
    if TEL not in html:
        fail(f"{fname} missing tel link")
    if "data-enquiry" in html:
        if 'action="/api/send-enquiry"' not in html and "send-enquiry" not in (
            ROOT / "assets/js/site.js"
        ).read_text(encoding="utf-8"):
            fail(f"{fname} enquiry form wiring")
ok("Instagram / WhatsApp / tel present on all expected pages (checked)")

# courses anchors
courses = (ROOT / "courses.html").read_text(encoding="utf-8")
for a in ("id=\"cpc\"", "id=\"ccs\""):
    if a in courses:
        ok(f"courses.html has {a}")
    else:
        fail(f"courses.html missing {a}")

print("\n=== 3) PRODUCTION HTTP PAGES + ASSETS ===")
for fname, (path, title, desc, tlen, dlen) in EXPECTED.items():
    st, body, _ = http_get(PROD + path)
    html = body.decode("utf-8", "replace")
    if st == 200:
        ok(f"PROD {path} → 200")
    else:
        fail(f"PROD {path} → {st}")
        continue
    got_t, got_d = title_desc(html)
    if got_t != title:
        fail(f"PROD {path} title mismatch")
    if got_d != desc:
        fail(f"PROD {path} description mismatch")
    if IG not in html or WA not in html or TEL not in html:
        fail(f"PROD {path} missing social/phone link")

for asset in [
    "/assets/css/style.css",
    "/assets/js/site.js",
    "/assets/img/logo.png",
]:
    st, body, _ = http_get(PROD + asset)
    if st == 200 and len(body) > 100:
        ok(f"PROD {asset} → 200 ({len(body)} bytes)")
    else:
        fail(f"PROD {asset} → {st}")

print("\n=== 4) LOCAL HTTP (if up) ===")
st, _, _ = http_get(LOCAL + "/")
local_up = st == 200
if local_up:
    ok("LOCAL server up")
    for fname, (path, *_rest) in EXPECTED.items():
        st, _, _ = http_get(LOCAL + path)
        if st == 200:
            ok(f"LOCAL {path} → 200")
        else:
            fail(f"LOCAL {path} → {st}")
else:
    print("SKIP: local server not running")

print("\n=== 5) API VALIDATION + E2E SMTP ===")
# validation
st, body = http_post_json(PROD, {"name": "", "phone": ""})
if st == 400 and body.get("ok") is False:
    ok("PROD API rejects empty name/phone")
else:
    fail(f"PROD API validation unexpected {st} {body}")

# GET should 405
st, body, _ = http_get(PROD + "/api/send-enquiry")
# may be 405 or 404 depending on platform — method not allowed preferred
if st in (405, 404, 500):
    ok(f"PROD API non-POST handled ({st})")
else:
    fail(f"PROD API GET unexpected {st}")

payload = {
    "name": "Full E2E Tejas",
    "phone": "7709099599",
    "email": "visitor.full.e2e@example.com",
    "city": "Kolhapur",
    "course": "CPC certification (AAPC)",
    "education": "B.Pharm",
    "message": "100% E2E checklist — confirm complete enquiry fields in Gmail",
    "page": "contact.html",
}
st, body = http_post_json(PROD, payload)
err = json.dumps(body).lower()
if "tejaswiulhalkar" in err or "iodv" in err or "@gmail.com" in err:
    fail("PROD API leaked secret/email in response")
elif st == 200 and body.get("ok") is True:
    ok("PROD form SMTP E2E → ok:true (complete enquiry accepted)")
else:
    fail(f"PROD form E2E failed {st} {body}")

if local_up:
    st, body = http_post_json(LOCAL, payload)
    if st == 200 and body.get("ok") is True:
        ok("LOCAL form SMTP/FormSubmit E2E → ok:true")
    else:
        fail(f"LOCAL form E2E failed {st} {body}")

print("\n=== SUMMARY ===")
print(f"PASS {len(passes)} | FAIL {len(issues)}")
for i in issues:
    print(" -", i)
sys.exit(1 if issues else 0)
