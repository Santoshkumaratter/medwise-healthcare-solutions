"""Final credential-free QA for MedWise (Tejas checklist minus live Gmail delivery)."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "website"
BASE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "qa-results"
OUT.mkdir(exist_ok=True)

EXPECTED = {
    "index.html": (
        "/",
        "Best Medical Coding Class in Kolhapur | CPC & CCS Training",
        "The best medical coding class in Kolhapur. AAPC CPC and AHIMA CCS certification training for Kolhapur, Sangli, Satara and Belgaum students. 100% placement.",
    ),
    "about.html": (
        "/about.html",
        "About MedWise — Medical Coding Institute in Kolhapur",
        "MedWise is Kolhapur's specialist medical coding institute in Rajarampuri: practising certified coders as faculty, batches of 20, and full placement support.",
    ),
    "courses.html": (
        "/courses.html",
        "CPC & CCS Medical Coding Courses in Kolhapur | MedWise",
        "Full CPC (AAPC) and CCS (AHIMA) syllabus, batch timings and fee structure at Kolhapur's specialist medical coding institute. 100% placement guarantee.",
    ),
    "contact.html": (
        "/contact.html",
        "Contact MedWise | Medical Coding Class in Kolhapur",
        "Visit MedWise at Yashodhara Apartment, Rajarampuri 6th Lane, Kolhapur 416008. Call or WhatsApp 7709099599 to book a free medical coding demo class.",
    ),
    "medical-coding-classes-in-kolhapur.html": (
        "/medical-coding-classes-in-kolhapur.html",
        "Medical Coding Classes in Kolhapur — Batches & Fees",
        "Medical coding classes in Kolhapur at Rajarampuri 6th Lane. Weekday, evening and weekend CPC and CCS batches of 20 students, with 100% placement guarantee.",
    ),
    "medical-coding-classes-in-sangli.html": (
        "/medical-coding-classes-in-sangli.html",
        "Medical Coding Classes in Sangli & Miraj | MedWise",
        "Medical coding classes for Sangli, Miraj and Ichalkaranji students — weekend classroom batches in Kolhapur or live online CPC and CCS training with placement.",
    ),
    "medical-coding-classes-in-satara.html": (
        "/medical-coding-classes-in-satara.html",
        "Medical Coding Classes in Satara & Karad | MedWise",
        "Medical coding classes for Satara and Karad students. Live online CPC and CCS certification training from Kolhapur's specialist institute, with placement.",
    ),
    "medical-coding-classes-in-belgaum.html": (
        "/medical-coding-classes-in-belgaum.html",
        "Medical Coding Classes in Belgaum (Belagavi) | MedWise",
        "Medical coding classes for Belgaum, Belagavi, Nipani and Chikodi students. CPC and CCS training online or in weekend Kolhapur batches, with placement support.",
    ),
}

IG = "https://www.instagram.com/medwisehealthcaresolutions/"
WA = "https://wa.me/917709099599"
TEL = "tel:+917709099599"

issues = []
passes = []


def ok(m: str) -> None:
    passes.append(m)
    print("PASS:", m)


def fail(m: str) -> None:
    issues.append(m)
    print("FAIL:", m)


def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "MedWiseFinalQA/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b""


def http_json(payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/send-enquiry",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MedWiseFinalQA/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def scan_public_secrets() -> None:
    print("\n=== Public secret / email leak scan ===")
    files = list(ROOT.glob("*.html")) + [
        ROOT / "assets/js/site.js",
        ROOT / "assets/css/style.css",
        ROOT / "vercel.json",
        ROOT / "package.json",
    ]
    forbidden = [
        r"GMAIL_APP_PASSWORD\s*=\s*\S+",
        r"formsubmit\.co",
        r"info@medwisehealthcaresolutions\.in",
        r"mailto:",
        r"AIza[0-9A-Za-z\-_]{20,}",
    ]
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for pat in forbidden:
            if re.search(pat, text, re.I):
                fail(f"{f.name}: forbidden pattern {pat}")
        for m in re.finditer(
            r"(?<![\w./-])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text
        ):
            email = m.group(1)
            fail(f"{f.name}: business/email address visible: {email}")

    js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
    if "/api/send-enquiry" in js and "GMAIL" not in js and "nodemailer" not in js:
        ok("Client JS calls API only; no mail secrets")
    else:
        fail("Client JS mail wiring incorrect")

    api = (ROOT / "api/send-enquiry.js").read_text(encoding="utf-8")
    if "process.env.GMAIL_USER" in api and "process.env.GMAIL_APP_PASSWORD" in api:
        ok("API reads credentials from env only")
    else:
        fail("API missing env-based credentials")
    # ensure no hardcoded password-looking strings
    if re.search(r"pass\s*[:=]\s*['\"][^'\"]+['\"]", api, re.I):
        fail("API appears to hardcode a password")
    else:
        ok("API has no hardcoded password")


def static_pages() -> None:
    print("\n=== 8 pages + exact meta + links ===")
    for fn, (path, title, desc) in EXPECTED.items():
        html = (ROOT / fn).read_text(encoding="utf-8")
        t = re.search(r"<title>(.*?)</title>", html).group(1)
        d = re.search(r'<meta name="description" content="(.*?)"', html).group(1)
        if t == title and d == desc:
            ok(f"{fn}: exact meta ({len(t)}/{len(d)})")
        else:
            fail(f"{fn}: meta mismatch")
        for need in (IG, WA, TEL, 'data-enquiry', "assets/js/site.js"):
            if need not in html:
                fail(f"{fn}: missing {need}")
        if "data-go=" in html:
            fail(f"{fn}: leftover SPA data-go")
        st, _ = http_get(BASE + path)
        if st == 200:
            ok(f"HTTP 200 {path}")
        else:
            fail(f"HTTP {st} {path}")

    courses = (ROOT / "courses.html").read_text(encoding="utf-8")
    if 'id="cpc"' in courses and 'id="ccs"' in courses:
        ok("courses #cpc/#ccs anchors present")
    else:
        fail("courses anchors missing")


def api_validation() -> None:
    print("\n=== API validation / response mapping ===")
    st, body = http_json({"name": "", "phone": ""})
    if st == 400 and body.get("ok") is False and "name and phone" in body.get("error", "").lower():
        ok("API required-field validation (400)")
    else:
        fail(f"API validation unexpected: {st} {body}")

    st, body = http_json(
        {
            "name": "QA Visitor",
            "phone": "7709099599",
            "email": "visitor.test@example.com",
            "city": "Kolhapur",
            "course": "CPC certification (AAPC)",
            "education": "B.Pharm",
            "message": "Optional visitor email forward test",
            "page": "Final QA",
        }
    )
    err = str(body.get("error", ""))
    if "@" in err or "GMAIL" in err or "password" in err.lower():
        fail(f"API error leaked secret/email: {body}")
    if st == 200 and body.get("ok") is True:
        ok("API send succeeded (Gmail configured + delivered)")
    elif st in (500, 502) and body.get("ok") is False:
        fail(
            "PENDING TEJAS: Gmail not configured in env yet — live delivery not verified. "
            f"Safe client error returned: {body}"
        )
    else:
        fail(f"Unexpected API send response: {st} {body}")


def browser_forms() -> None:
    print("\n=== Browser form QA (desktop + mobile) ===")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for label, vp in (
            ("desktop", {"width": 1440, "height": 900}),
            ("mobile", {"width": 390, "height": 844}),
        ):
            context = browser.new_context(
                viewport=vp,
                is_mobile=(label == "mobile"),
                has_touch=(label == "mobile"),
            )
            page = context.new_page()
            console_err = []
            page.on(
                "console",
                lambda msg: console_err.append(msg.text) if msg.type == "error" else None,
            )

            page.goto(BASE + "/contact.html", wait_until="networkidle")
            html = page.content()
            if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html):
                # optional visitor email field shouldn't contain a prefilled address;
                # but type=email label is fine. Check for @domain patterns in visible text nodes.
                emails = re.findall(
                    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html
                )
                if emails:
                    fail(f"[{label}] email address(es) in rendered contact HTML: {emails}")
            else:
                ok(f"[{label}] no email addresses in contact HTML")

            form = page.locator("form[data-enquiry]").first
            # empty validation
            form.locator('button[type="submit"]').click()
            page.wait_for_timeout(250)
            status = form.locator(".form-status").inner_text()
            if "name and phone" in status.lower():
                ok(f"[{label}] required validation UI")
            else:
                fail(f"[{label}] required validation UI missing: {status!r}")

            # filled submit with optional visitor email
            form.locator('input[name="name"]').fill("Browser QA User")
            form.locator('input[name="phone"]').fill("7709099599")
            if form.locator('input[name="email"]').count():
                form.locator('input[name="email"]').fill("visitor.test@example.com")
            with page.expect_response(lambda r: "/api/send-enquiry" in r.url, timeout=30000) as ri:
                form.locator('button[type="submit"]').click()
            resp = ri.value
            body = resp.json()
            page.wait_for_timeout(300)
            status = form.locator(".form-status").inner_text()
            print(f"[{label}] API {resp.status} {body} | UI {status!r}")

            if "@" in status and "visitor.test" not in status:
                # success message shouldn't show Tejas email; visitor email also shouldn't appear in status
                fail(f"[{label}] status leaked an email: {status!r}")

            if resp.status == 200 and body.get("ok") is True:
                if "Thanks" in status and "received your enquiry" in status:
                    ok(f"[{label}] success UI matches API ok")
                else:
                    fail(f"[{label}] API ok but UI not success: {status!r}")
            elif body.get("ok") is False:
                if "Thanks" in status:
                    fail(f"[{label}] API failed but UI shows success")
                elif status.strip() and ("Could not send" in status or "WhatsApp" in status or body.get("error", "") in status):
                    ok(f"[{label}] error UI matches API failure (credentials pending or SMTP fail)")
                else:
                    fail(f"[{label}] error UI mismatch: {status!r} vs {body}")
            else:
                fail(f"[{label}] unexpected API/UI pair")

            # optional email included in request payload
            # (already filled above; ensure field exists on contact)
            if form.locator('input[name="email"]').count():
                ok(f"[{label}] optional visitor email field present")
            else:
                fail(f"[{label}] optional visitor email field missing on contact")

            page.screenshot(path=str(OUT / f"final-contact-{label}.png"), full_page=True)

            real_console = [e for e in console_err if "favicon" not in e.lower()]
            if real_console:
                fail(f"[{label}] console errors: {real_console[:3]}")
            else:
                ok(f"[{label}] no console errors")

            context.close()
        browser.close()


def main() -> int:
    # server readiness
    for _ in range(20):
        try:
            st, _ = http_get(BASE + "/")
            if st == 200:
                break
        except Exception:
            pass
        import time

        time.sleep(0.25)
    else:
        print("Server not running at", BASE)
        return 2

    scan_public_secrets()
    static_pages()
    api_validation()
    browser_forms()

    report = {"pass": passes, "fail": issues}
    (OUT / "final-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(f"PASS {len(passes)} FAIL {len(issues)}")
    for i in issues:
        print("ISSUE:", i)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
