"""MedWise final QA — Tejas requirements checklist + browser UI tests."""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent / "website"
BASE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent / "qa-results"
OUT.mkdir(exist_ok=True)

PAGES = {
    "index.html": {
        "path": "/",
        "alt": "/index.html",
        "title": "Best Medical Coding Class in Kolhapur | CPC & CCS Training",
        "description": "The best medical coding class in Kolhapur. AAPC CPC and AHIMA CCS certification training for Kolhapur, Sangli, Satara and Belgaum students. 100% placement.",
        "nav": "home",
    },
    "about.html": {
        "path": "/about.html",
        "title": "About MedWise — Medical Coding Institute in Kolhapur",
        "description": "MedWise is Kolhapur's specialist medical coding institute in Rajarampuri: practising certified coders as faculty, batches of 20, and full placement support.",
        "nav": "about",
    },
    "courses.html": {
        "path": "/courses.html",
        "title": "CPC & CCS Medical Coding Courses in Kolhapur | MedWise",
        "description": "Full CPC (AAPC) and CCS (AHIMA) syllabus, batch timings and fee structure at Kolhapur's specialist medical coding institute. 100% placement guarantee.",
        "nav": "courses",
    },
    "contact.html": {
        "path": "/contact.html",
        "title": "Contact MedWise | Medical Coding Class in Kolhapur",
        "description": "Visit MedWise at Yashodhara Apartment, Rajarampuri 6th Lane, Kolhapur 416008. Call or WhatsApp 7709099599 to book a free medical coding demo class.",
        "nav": "contact",
    },
    "medical-coding-classes-in-kolhapur.html": {
        "path": "/medical-coding-classes-in-kolhapur.html",
        "title": "Medical Coding Classes in Kolhapur — Batches & Fees",
        "description": "Medical coding classes in Kolhapur at Rajarampuri 6th Lane. Weekday, evening and weekend CPC and CCS batches of 20 students, with 100% placement guarantee.",
        "nav": None,
    },
    "medical-coding-classes-in-sangli.html": {
        "path": "/medical-coding-classes-in-sangli.html",
        "title": "Medical Coding Classes in Sangli & Miraj | MedWise",
        "description": "Medical coding classes for Sangli, Miraj and Ichalkaranji students — weekend classroom batches in Kolhapur or live online CPC and CCS training with placement.",
        "nav": None,
    },
    "medical-coding-classes-in-satara.html": {
        "path": "/medical-coding-classes-in-satara.html",
        "title": "Medical Coding Classes in Satara & Karad | MedWise",
        "description": "Medical coding classes for Satara and Karad students. Live online CPC and CCS certification training from Kolhapur's specialist institute, with placement.",
        "nav": None,
    },
    "medical-coding-classes-in-belgaum.html": {
        "path": "/medical-coding-classes-in-belgaum.html",
        "title": "Medical Coding Classes in Belgaum (Belagavi) | MedWise",
        "description": "Medical coding classes for Belgaum, Belagavi, Nipani and Chikodi students. CPC and CCS training online or in weekend Kolhapur batches, with placement support.",
        "nav": None,
    },
}

EXPECTED_IG = "https://www.instagram.com/medwisehealthcaresolutions/"
EXPECTED_WA = "https://wa.me/917709099599"
EXPECTED_TEL = "tel:+917709099599"
EXPECTED_FORM = "https://formsubmit.co/ajax/info@medwisehealthcaresolutions.in"

issues: list[str] = []
passes: list[str] = []


def _safe_print(prefix: str, msg: str) -> None:
    line = f"{prefix}: {msg}".replace("→", "->").replace("—", "-").replace("…", "...")
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))


def ok(msg: str) -> None:
    passes.append(msg)
    _safe_print("PASS", msg)


def fail(msg: str) -> None:
    issues.append(msg)
    _safe_print("FAIL", msg)


def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "MedWiseQA/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            body = res.read()
            return res.status, dict(res.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read() if e.fp else b""
    except Exception as e:
        return None, {}, str(e).encode()


def check_static() -> None:
    print("\n=== STATIC / HTTP CHECKS ===")
    # PHP must be gone
    if (ROOT / "send-enquiry.php").exists():
        fail("send-enquiry.php still present (should be FormSubmit only)")
    else:
        ok("No PHP handler present")

    js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
    if EXPECTED_FORM in js:
        ok("FormSubmit endpoint targets info@medwisehealthcaresolutions.in")
    else:
        fail(f"Form endpoint missing/incorrect in site.js. Expected {EXPECTED_FORM}")
    if "send-enquiry.php" in js:
        fail("site.js still references send-enquiry.php")

    # logo
    logo = ROOT / "assets/img/logo.png"
    if logo.exists() and logo.stat().st_size > 1000:
        ok(f"logo.png present ({logo.stat().st_size} bytes)")
    else:
        fail("logo.png missing or empty")

    css = ROOT / "assets/css/style.css"
    if css.exists() and css.stat().st_size > 1000:
        ok(f"style.css present ({css.stat().st_size} bytes)")
    else:
        fail("style.css missing")

    for filename, meta in PAGES.items():
        fpath = ROOT / filename
        if not fpath.exists():
            fail(f"Missing file {filename}")
            continue
        html = fpath.read_text(encoding="utf-8")

        title_m = re.search(r"<title>(.*?)</title>", html)
        desc_m = re.search(r'<meta name="description" content="(.*?)"', html)
        title = title_m.group(1) if title_m else ""
        desc = desc_m.group(1) if desc_m else ""
        if title == meta["title"]:
            ok(f"{filename}: exact title ({len(title)} chars)")
        else:
            fail(f"{filename}: title mismatch\n  got: {title!r}\n  exp: {meta['title']!r}")
        if desc == meta["description"]:
            ok(f"{filename}: exact description ({len(desc)} chars)")
        else:
            fail(f"{filename}: description mismatch\n  got: {desc!r}\n  exp: {meta['description']!r}")

        # no leftover SPA attrs
        if "data-go=" in html:
            fail(f"{filename}: leftover data-go SPA navigation")
        if "preview-bar" in html or "Interactive preview" in html:
            fail(f"{filename}: preview-bar leftover")

        # required links
        if EXPECTED_IG not in html and filename in ("index.html", "contact.html"):
            # Instagram must appear at least on home/contact/footer - footer is on all
            pass
        if EXPECTED_IG not in html:
            fail(f"{filename}: Instagram URL missing")
        else:
            ok(f"{filename}: Instagram URL present")

        if EXPECTED_WA not in html:
            fail(f"{filename}: WhatsApp wa.me/917709099599 missing")
        else:
            ok(f"{filename}: WhatsApp link present")

        if EXPECTED_TEL not in html:
            fail(f"{filename}: tel:+917709099599 missing")
        else:
            ok(f"{filename}: phone tel link present")

        # form present
        if 'data-enquiry' not in html:
            fail(f"{filename}: enquiry form missing")
        else:
            ok(f"{filename}: enquiry form present")

        # assets referenced
        for asset in ("assets/css/style.css", "assets/js/site.js", "assets/img/logo.png"):
            if asset not in html:
                fail(f"{filename}: missing reference to {asset}")

        # HTTP 200
        status, _, body = http_get(BASE + meta["path"])
        if status == 200:
            ok(f"HTTP {status} {meta['path']}")
        else:
            fail(f"HTTP {status} for {meta['path']} ({body[:120]!r})")

        # also check index.html path if home
        if filename == "index.html":
            s2, _, _ = http_get(BASE + "/index.html")
            if s2 == 200:
                ok("HTTP 200 /index.html")
            else:
                fail(f"HTTP {s2} /index.html")

        # collect internal hrefs
        hrefs = re.findall(r'href="([^"]*)"', html)
        for href in hrefs:
            if href.startswith(("http://", "https://", "tel:", "mailto:", "data:", "javascript:")):
                continue
            if href.startswith("#"):
                # in-page anchors: verify id exists on same page when not empty
                aid = href[1:]
                if aid and f'id="{aid}"' not in html:
                    fail(f"{filename}: missing in-page anchor id=#{aid}")
                continue
            rel = href.split("?")[0].split("#")[0]
            if not rel:
                continue
            if not (ROOT / rel).exists():
                fail(f"{filename}: broken local href {href}")

    # courses anchors
    courses = (ROOT / "courses.html").read_text(encoding="utf-8")
    if 'id="cpc"' in courses and 'id="ccs"' in courses:
        ok("courses.html has #cpc and #ccs anchors")
    else:
        fail("courses.html missing id=cpc and/or id=ccs")

    # asset HTTP
    for asset in ("/assets/css/style.css", "/assets/js/site.js", "/assets/img/logo.png"):
        st, headers, body = http_get(BASE + asset)
        if st == 200 and len(body) > 100:
            ok(f"HTTP 200 asset {asset} ({len(body)} bytes)")
        else:
            fail(f"Asset failed {asset}: status={st} len={len(body)}")


def check_browser() -> None:
    print("\n=== BROWSER UI CHECKS (Playwright) ===")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("Playwright not installed")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for label, viewport in (
            ("desktop", {"width": 1440, "height": 900}),
            ("mobile", {"width": 390, "height": 844}),
        ):
            context = browser.new_context(
                viewport=viewport,
                device_scale_factor=1,
                is_mobile=(label == "mobile"),
                has_touch=(label == "mobile"),
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
                    if label == "mobile"
                    else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            failed_requests: list[str] = []

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.on(
                "requestfailed",
                lambda req: failed_requests.append(f"{req.url} :: {req.failure}"),
            )

            # Home
            page.goto(BASE + "/", wait_until="networkidle", timeout=30000)
            page.screenshot(path=str(OUT / f"home-{label}.png"), full_page=False)
            title = page.title()
            if title == PAGES["index.html"]["title"]:
                ok(f"[{label}] Home document title correct")
            else:
                fail(f"[{label}] Home title wrong: {title!r}")

            # logo visible
            logo = page.locator(".brand img, .foot-brand img").first
            if logo.count() and logo.is_visible():
                ok(f"[{label}] Logo visible")
            else:
                fail(f"[{label}] Logo not visible")

            # nav / menu
            if label == "mobile":
                toggle = page.locator(".nav-toggle")
                if toggle.is_visible():
                    ok(f"[{label}] Menu toggle visible")
                    toggle.click()
                    page.wait_for_timeout(300)
                    if page.locator("#primary-nav").evaluate("el => el.classList.contains('open')"):
                        ok(f"[{label}] Mobile nav opens")
                    else:
                        fail(f"[{label}] Mobile nav did not open")
                else:
                    fail(f"[{label}] Menu toggle not visible")

            # Navigate all main pages via links
            nav_checks = [
                ("About us", "/about.html", PAGES["about.html"]["title"]),
                ("What we offer", "/courses.html", PAGES["courses.html"]["title"]),
                ("Contact us", "/contact.html", PAGES["contact.html"]["title"]),
                ("Home", "/", PAGES["index.html"]["title"]),
            ]
            for link_text, expect_path, expect_title in nav_checks:
                if label == "mobile":
                    # ensure nav open
                    nav = page.locator("#primary-nav")
                    if not nav.evaluate("el => el.classList.contains('open')"):
                        if page.locator(".nav-toggle").is_visible():
                            page.locator(".nav-toggle").click()
                            page.wait_for_timeout(200)
                link = page.locator(f'#primary-nav a:has-text("{link_text}")').first
                if link.count() == 0:
                    fail(f"[{label}] Nav link missing: {link_text}")
                    continue
                link.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(200)
                if expect_path == "/":
                    path_ok = (
                        page.url.rstrip("/").endswith(":8765")
                        or page.url.endswith("/")
                        or page.url.endswith("/index.html")
                    )
                else:
                    path_ok = expect_path in page.url
                if path_ok and page.title() == expect_title:
                    ok(f"[{label}] Nav '{link_text}' -> {expect_path}")
                else:
                    fail(f"[{label}] Nav '{link_text}' failed: url={page.url} title={page.title()!r}")

            # City pages from footer
            city_links = [
                ("Kolhapur", "/medical-coding-classes-in-kolhapur.html"),
                ("Sangli", "/medical-coding-classes-in-sangli.html"),
                ("Satara", "/medical-coding-classes-in-satara.html"),
                ("Belgaum", "/medical-coding-classes-in-belgaum.html"),
            ]
            page.goto(BASE + "/", wait_until="networkidle")
            for text, path in city_links:
                loc = page.locator(f'footer a[href="{path.lstrip("/")}"] , footer a[href="{path}"]').first
                # href is relative without leading slash in our HTML
                loc = page.locator(f'footer .foot-grid a:has-text("{text}")').first
                if loc.count() == 0:
                    fail(f"[{label}] Footer city link missing: {text}")
                    continue
                with page.expect_navigation():
                    loc.click()
                if path in page.url:
                    ok(f"[{label}] Footer '{text}' → {path}")
                else:
                    fail(f"[{label}] Footer '{text}' wrong url {page.url}")
                page.screenshot(path=str(OUT / f"city-{text.lower()}-{label}.png"), full_page=False)

            # courses #cpc #ccs
            page.goto(BASE + "/courses.html#cpc", wait_until="networkidle")
            cpc = page.locator("#cpc")
            if cpc.count() and cpc.is_visible():
                ok(f"[{label}] #cpc section visible")
            else:
                fail(f"[{label}] #cpc section not visible")
            page.goto(BASE + "/courses.html#ccs", wait_until="networkidle")
            if page.locator("#ccs").count() and page.locator("#ccs").is_visible():
                ok(f"[{label}] #ccs section visible")
            else:
                fail(f"[{label}] #ccs section not visible")

            # Instagram / WhatsApp / tel href attributes (don't necessarily open external)
            page.goto(BASE + "/contact.html", wait_until="networkidle")
            ig = page.locator(f'a[href="{EXPECTED_IG}"]')
            wa = page.locator(f'a[href="{EXPECTED_WA}"]')
            tel = page.locator(f'a[href="{EXPECTED_TEL}"]')
            if ig.count() > 0:
                ok(f"[{label}] Instagram href correct on contact")
            else:
                fail(f"[{label}] Instagram href incorrect/missing on contact")
            if wa.count() > 0:
                ok(f"[{label}] WhatsApp href correct on contact")
            else:
                fail(f"[{label}] WhatsApp href incorrect/missing on contact")
            if tel.count() > 0:
                ok(f"[{label}] Phone href correct on contact")
            else:
                fail(f"[{label}] Phone href incorrect/missing on contact")

            # External Instagram HEAD
            # Form submit test on home
            page.goto(BASE + "/", wait_until="networkidle")
            page.locator("#home-apply").scroll_into_view_if_needed()
            form = page.locator("form[data-enquiry]").first
            form.locator('input[name="name"]').fill("QA Test User")
            form.locator('input[name="phone"]').fill("7709099599")
            # city select if present
            if form.locator('select[name="city"]').count():
                form.locator('select[name="city"]').select_option(index=0)
            if form.locator('input[name="education"]').count():
                form.locator('input[name="education"]').fill("B.Pharm")

            # Intercept FormSubmit request
            with page.expect_response(
                lambda r: "formsubmit.co" in r.url, timeout=45000
            ) as resp_info:
                form.locator('button[type="submit"]').click()
            resp = resp_info.value
            body_text = ""
            try:
                body_text = resp.text()
            except Exception:
                pass
            status_el = form.locator(".form-status")
            status_text = status_el.inner_text() if status_el.count() else ""
            print(f"[{label}] FormSubmit status={resp.status} body={body_text[:300]!r} ui={status_text!r}")

            if resp.status in (200, 201) or ("success" in body_text.lower()):
                ok(f"[{label}] Form submitted to FormSubmit (HTTP {resp.status})")
            else:
                fail(f"[{label}] FormSubmit response not OK: HTTP {resp.status} body={body_text[:200]!r}")

            # UI should not stay stuck on Sending…
            page.wait_for_timeout(500)
            status_text = status_el.inner_text() if status_el.count() else ""
            btn_text = form.locator('button[type="submit"]').inner_text()
            if "Sending" in btn_text:
                fail(f"[{label}] Submit button stuck on Sending…")
            else:
                ok(f"[{label}] Submit button restored after form attempt")

            if "Could not send" in status_text and resp.status not in (200, 201):
                fail(f"[{label}] Form UI shows error: {status_text!r}")
            elif status_text:
                ok(f"[{label}] Form status message shown: {status_text!r}")

            # Empty validation
            page.goto(BASE + "/contact.html", wait_until="networkidle")
            cform = page.locator("form[data-enquiry]").first
            cform.locator('button[type="submit"]').click()
            page.wait_for_timeout(300)
            cstatus = cform.locator(".form-status").inner_text()
            if "name and phone" in cstatus.lower() or "Please add" in cstatus:
                ok(f"[{label}] Empty form validation works")
            else:
                fail(f"[{label}] Empty form validation missing/wrong: {cstatus!r}")

            # Layout overflow check on home
            page.goto(BASE + "/", wait_until="networkidle")
            overflow = page.evaluate(
                """() => {
                  const doc = document.documentElement;
                  return {
                    scrollWidth: doc.scrollWidth,
                    clientWidth: doc.clientWidth,
                    overflow: doc.scrollWidth > doc.clientWidth + 2
                  };
                }"""
            )
            if overflow["overflow"]:
                fail(f"[{label}] Horizontal overflow: scrollWidth={overflow['scrollWidth']} clientWidth={overflow['clientWidth']}")
            else:
                ok(f"[{label}] No horizontal overflow")

            # Screenshots of key pages
            for path, name in (
                ("/", "home"),
                ("/about.html", "about"),
                ("/courses.html", "courses"),
                ("/contact.html", "contact"),
            ):
                page.goto(BASE + path, wait_until="networkidle")
                page.screenshot(path=str(OUT / f"{name}-{label}-full.png"), full_page=True)

            # Console / network issues (filter noise)
            real_console = [e for e in console_errors if "favicon" not in e.lower()]
            real_failed = [e for e in failed_requests if "favicon" not in e.lower()]
            if page_errors:
                fail(f"[{label}] pageerror: {page_errors}")
            else:
                ok(f"[{label}] No page JS errors")
            if real_console:
                fail(f"[{label}] console errors: {real_console[:5]}")
            else:
                ok(f"[{label}] No console errors")
            if real_failed:
                fail(f"[{label}] failed requests: {real_failed[:5]}")
            else:
                ok(f"[{label}] No failed network requests")

            context.close()

        # External Instagram / WhatsApp reachability (HEAD/GET)
        browser.close()

    # External link checks via HTTP
    print("\n=== EXTERNAL LINK REACHABILITY ===")
    for url, name in (
        (EXPECTED_IG, "Instagram profile"),
        (EXPECTED_WA, "WhatsApp wa.me"),
    ):
        st, headers, body = http_get(url)
        # Instagram often 200 or 302; wa.me often 200/302
        if st in (200, 301, 302, 303):
            ok(f"{name} reachable HTTP {st}")
        else:
            fail(f"{name} not reachable: status={st}")


def main() -> int:
    # wait for server
    for _ in range(30):
        st, _, _ = http_get(BASE + "/")
        if st == 200:
            break
        time.sleep(0.3)
    else:
        print("Server not up at", BASE)
        return 2

    check_static()
    check_browser()

    report = {
        "pass_count": len(passes),
        "fail_count": len(issues),
        "passes": passes,
        "issues": issues,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "report.txt").write_text(
        "PASSES\n" + "\n".join(f"- {p}" for p in passes) + "\n\nISSUES\n" + ("\n".join(f"- {i}" for i in issues) or "None") + "\n",
        encoding="utf-8",
    )

    print("\n=== SUMMARY ===")
    print(f"PASS: {len(passes)}  FAIL: {len(issues)}")
    if issues:
        print("ISSUES FOUND:")
        for i in issues:
            print(" -", i)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
