"""Verify: no public email addresses + form API flow."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "website"
BASE = os.environ.get("QA_BASE", "http://127.0.0.1:8765")

# Business / destination emails must not appear in public frontend files
FORBIDDEN_PATTERNS = [
    r"info@medwisehealthcaresolutions\.in",
    r"no-reply@medwisehealthcaresolutions\.in",
    r"formsubmit\.co/ajax/",
    r"mailto:",
]

CLIENT_FILES = list(ROOT.glob("*.html")) + [
    ROOT / "assets" / "js" / "site.js",
    ROOT / "assets" / "css" / "style.css",
]

issues = []
passes = []


def ok(m):
    passes.append(m)
    print("PASS:", m)


def fail(m):
    issues.append(m)
    print("FAIL:", m)


def http_json(method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "MedWiseFormQA/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            body = res.read().decode("utf-8", "replace")
            return res.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed


print("=== Public email leak check ===")
for f in CLIENT_FILES:
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    # Ignore visitor optional email input markup
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, text, re.I):
            fail(f"{f.name}: forbidden pattern {pat}")
    # Any @domain that looks like an email address displayed (exclude fonts.googleapis etc URLs)
    # Find user-facing emails: word@word.tld not inside href=https
    for m in re.finditer(r"(?<![\w./-])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text):
        email = m.group(1).lower()
        # allow nothing — Instagram handles use @name without domain
        if email.endswith((".com", ".in", ".net", ".org")):
            # skip if it's inside a comment about env? shouldn't be in client
            fail(f"{f.name}: email address found in public file: {email}")

# site.js must call API only
js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
if "/api/send-enquiry" in js:
    ok("site.js posts to /api/send-enquiry")
else:
    fail("site.js missing /api/send-enquiry")
if "formsubmit" in js.lower() or "gmail.com" in js.lower() or "medwisehealthcaresolutions.in" in js.lower():
    fail("site.js still contains email provider/address details")
else:
    ok("site.js has no email provider/address")

print("\n=== API behaviour ===")
# missing fields
st, body = http_json("POST", BASE + "/api/send-enquiry", {"name": "", "phone": ""})
if st == 400 and body.get("ok") is False:
    ok("API validates name/phone")
else:
    fail(f"API validation unexpected: {st} {body}")

# configured send attempt
st, body = http_json(
    "POST",
    BASE + "/api/send-enquiry",
    {
        "name": "QA Test User",
        "phone": "7709099599",
        "city": "Kolhapur",
        "course": "CPC certification (AAPC)",
        "education": "B.Pharm",
        "message": "Automated QA test — please ignore",
        "page": "QA",
    },
)
print("Send response:", st, body)

if st == 200 and body.get("ok") is True:
    ok("Form API mail send succeeded (Gmail delivered)")
elif st == 500 and body.get("ok") is False and "@" not in str(body.get("error", "")):
    fail(
        "BLOCKER: GMAIL_USER / GMAIL_APP_PASSWORD not set in website/.env.local "
        "(or Vercel env). Code path is safe (no email leaked), but live delivery cannot be verified until Tejas Gmail credentials are provided."
    )
elif st == 502 and body.get("ok") is False:
    fail(
        "Gmail SMTP rejected the send. Check App Password / 2FA. API message: "
        + str(body)
    )
else:
    fail(f"Unexpected send response: {st} {body}")

# ensure HTML pages still 200
for path in ["/", "/contact.html", "/about.html"]:
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "MedWiseFormQA/1.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        if res.status == 200:
            ok(f"HTTP 200 {path}")
        else:
            fail(f"HTTP {res.status} {path}")

print("\n=== SUMMARY ===")
print(f"PASS {len(passes)} FAIL {len(issues)}")
for i in issues:
    print("ISSUE:", i)
sys.exit(1 if issues else 0)
