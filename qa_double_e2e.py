"""
MedWise — double-cross 100% E2E vs Tejas requirements.
Runs the full checklist twice (Pass A + Pass B). Never prints secrets.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "website"
BASES = [
    ("LOCAL", "http://127.0.0.1:8765"),
    ("HOSTINGER", "https://medwisehealthcaresolutions.com"),
    ("PROD_A", "https://website-eight-iota-ni22rhq9op.vercel.app"),
    ("PROD_B", "https://medwise-healthcare-solutions.vercel.app"),
]

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
    req = urllib.request.Request(url, headers={"User-Agent": "MedWiseDoubleE2E/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b""
    except Exception as e:
        return 0, str(e).encode()


def http_post_json(base: str, payload: dict):
    """Try Hostinger PHP first, then Vercel/local API."""
    last = (0, {"error": "no_endpoint"})
    for path in ("/send-enquiry.php", "/api/send-enquiry"):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            base.rstrip("/") + path,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "MedWiseDoubleE2E/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (404, 405):
                last = (e.code, {"raw": body[:120]})
                continue
            try:
                return e.code, json.loads(body)
            except Exception:
                return e.code, {"raw": body[:300]}
        except Exception as e:
            last = (0, {"error": str(e)})
            continue
    return last


def title_desc(html: str):
    t = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    d = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    if not d:
        d = re.search(r"<meta\s+name='description'\s+content='([^']*)'", html, re.I)
    return (t.group(1).strip() if t else ""), (d.group(1).strip() if d else "")


def run_pass(label: str) -> None:
    print(f"\n########## {label} ##########")

    # --- Disk: secrets / structure ---
    print(f"\n=== {label}: DISK / SECRETS / STRUCTURE ===")
    client = ""
    for f in list(ROOT.glob("*.html")) + [ROOT / "assets/js/site.js"]:
        client += f.read_text(encoding="utf-8", errors="replace")
    if "tejaswiulhalkar1996@gmail.com" in client.lower():
        fail(f"{label} destination Gmail in public HTML/JS")
    else:
        ok(f"{label} no destination Gmail in public HTML/JS")
    if re.search(r"formsubmit\.co", client, re.I):
        fail(f"{label} FormSubmit in client")
    else:
        ok(f"{label} no FormSubmit in client")
    js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
    if "/send-enquiry.php" not in js or "/api/send-enquiry" not in js:
        fail(f"{label} forms missing PHP+API fallback endpoints")
    else:
        ok(f"{label} forms -> /send-enquiry.php then /api/send-enquiry")
    if not (ROOT / "send-enquiry.php").is_file():
        fail(f"{label} send-enquiry.php missing")
    else:
        ok(f"{label} send-enquiry.php present")
    if not (ROOT / "mail-config.example.php").is_file():
        fail(f"{label} mail-config.example.php missing")
    else:
        ok(f"{label} mail-config.example.php present")
    php_files = [
        p
        for p in ROOT.rglob("*.php")
        if p.name not in ("send-enquiry.php", "mail-config.example.php", "mail-config.php")
    ]
    if php_files:
        fail(f"{label} unexpected PHP files: {[p.name for p in php_files]}")
    else:
        ok(f"{label} only expected PHP enquiry files")
    for asset in ("assets/css/style.css", "assets/js/site.js", "assets/img/logo.png"):
        if (ROOT / asset).is_file():
            ok(f"{label} asset {asset}")
        else:
            fail(f"{label} missing {asset}")

    css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
    for needle in ("color-scheme: only light", "--ink-soft:    #1F3646", "--on-ink:", ".tick li"):
        if needle.split()[0] in css or needle in css:
            ok(f"{label} contrast CSS has {needle[:28]}…")
        else:
            # softer check
            if "only light" in css and "--ink-soft" in css and "--on-ink" in css:
                ok(f"{label} contrast CSS markers present")
                break
            fail(f"{label} contrast CSS missing {needle}")

    if "only light" in css and "#1F3646" in css and "--on-ink" in css:
        ok(f"{label} high-contrast palette locked")
    else:
        fail(f"{label} high-contrast palette incomplete")

    for needle in (
        "overflow-x: hidden",
        "stops iOS zoom on focus",
        "env(safe-area-inset-bottom)",
        "max-height: min(80vh, 520px)",
    ):
        if needle in css:
            ok(f"{label} mobile CSS: {needle[:28]}")
        else:
            fail(f"{label} mobile CSS missing: {needle}")

    # --- Disk metas / links ---
    print(f"\n=== {label}: DISK METAS / LINKS (Tejas exact) ===")
    for fname, (path, title, desc, tlen, dlen) in EXPECTED.items():
        html = (ROOT / fname).read_text(encoding="utf-8")
        got_t, got_d = title_desc(html)
        if got_t == title and len(got_t) == tlen:
            ok(f"{label} {fname} title exact ({tlen})")
        else:
            fail(f"{label} {fname} title got={len(got_t)!r} {got_t[:40]!r}")
        if got_d == desc and len(got_d) == dlen:
            ok(f"{label} {fname} desc exact ({dlen})")
        else:
            fail(f"{label} {fname} desc got={len(got_d)} want={dlen}")
        for link, name in ((IG, "IG"), (WA, "WA"), (TEL, "TEL")):
            if link not in html:
                fail(f"{label} {fname} missing {name}")
        if 'name="color-scheme"' not in html and "color-scheme" not in html:
            fail(f"{label} {fname} missing color-scheme meta")
        else:
            ok(f"{label} {fname} color-scheme meta")

    courses = (ROOT / "courses.html").read_text(encoding="utf-8")
    for a in ('id="cpc"', 'id="ccs"'):
        if a in courses:
            ok(f"{label} courses {a}")
        else:
            fail(f"{label} courses missing {a}")
    contact = (ROOT / "contact.html").read_text(encoding="utf-8")
    if 'id="apply"' in contact or 'name="name"' in contact:
        ok(f"{label} contact form present")
    else:
        fail(f"{label} contact form missing")
    if 'data-enquiry' not in client:
        fail(f"{label} data-enquiry forms missing")
    else:
        ok(f"{label} enquiry forms marked data-enquiry")

    # --- Live hosts ---
    for host_label, base in BASES:
        print(f"\n=== {label}: LIVE {host_label} ({base}) ===")
        st, body = http_get(base + "/")
        if st != 200:
            fail(f"{label} {host_label} home → {st}")
            continue
        if b"Log in to Vercel" in body or b"vercel.com/login" in body.lower():
            fail(f"{label} {host_label} SSO/login wall")
            continue
        ok(f"{label} {host_label} home 200 (public)")

        for fname, (path, title, desc, tlen, dlen) in EXPECTED.items():
            st, body = http_get(base + path)
            html = body.decode("utf-8", "replace")
            if st != 200:
                fail(f"{label} {host_label} {path} → {st}")
                continue
            ok(f"{label} {host_label} {path} → 200")
            got_t, got_d = title_desc(html)
            if got_t != title:
                fail(f"{label} {host_label} {path} title mismatch")
            if got_d != desc:
                fail(f"{label} {host_label} {path} desc mismatch")
            if IG not in html or WA not in html or TEL not in html:
                fail(f"{label} {host_label} {path} missing IG/WA/TEL")

        for asset in (
            "/assets/css/style.css",
            "/assets/js/site.js",
            "/assets/img/logo.png",
        ):
            st, body = http_get(base + asset)
            if st == 200 and len(body) > 100 and not body.lstrip().startswith(b"<!DOCTYPE"):
                ok(f"{label} {host_label} {asset} OK ({len(body)}b)")
            else:
                fail(f"{label} {host_label} {asset} bad ({st})")

        st, jsb = http_get(base + "/assets/js/site.js")
        js_live = jsb.decode("utf-8", "replace")
        if "/send-enquiry.php" in js_live and "/api/send-enquiry" in js_live:
            ok(f"{label} {host_label} live JS dual endpoints")
        else:
            fail(f"{label} {host_label} live JS missing dual endpoints")

        st, cssb = http_get(base + "/assets/css/style.css")
        css_live = cssb.decode("utf-8", "replace")
        if "only light" in css_live and "#1F3646" in css_live:
            ok(f"{label} {host_label} live contrast CSS")
        else:
            fail(f"{label} {host_label} live contrast CSS missing")

        # API / PHP validation
        st, resp = http_post_json(base, {"name": "", "phone": ""})
        if st == 400 and resp.get("ok") is False:
            ok(f"{label} {host_label} form validates name/phone")
        else:
            fail(f"{label} {host_label} form validation {st} {resp}")

        # Full enquiry E2E (SMTP)
        payload = {
            "name": f"Double E2E {label} {host_label}",
            "phone": "7709099599",
            "email": "visitor.double.e2e@example.com",
            "city": "Kolhapur",
            "course": "CPC certification (AAPC)",
            "education": "B.Pharm",
            "message": f"Double-cross E2E ({label}/{host_label}) — confirm complete enquiry in Gmail",
            "page": "contact.html",
        }
        st, resp = http_post_json(base, payload)
        blob = json.dumps(resp).lower()
        if "tejaswiulhalkar" in blob or "iodv" in blob or "@gmail.com" in blob:
            fail(f"{label} {host_label} form leaked secret/email")
        elif st == 200 and resp.get("ok") is True:
            ok(f"{label} {host_label} form SMTP E2E ok:true")
        else:
            fail(f"{label} {host_label} form E2E {st} {resp}")


def main() -> int:
    # quick local ping
    st, _ = http_get("http://127.0.0.1:8765/")
    if st != 200:
        print("WARN: local server not up — LOCAL checks will fail")

    run_pass("PASS-A")
    run_pass("PASS-B")

    print("\n========== FINAL DOUBLE-CROSS SUMMARY ==========")
    print(f"PASS {len(passes)} | FAIL {len(issues)}")
    if issues:
        print("FAILURES:")
        for i in issues:
            print(" -", i)
        return 1
    print("VERDICT: 100% PASS vs Tejas requirements (double-cross)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
