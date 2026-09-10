"""E2E enquiry test against local + Vercel production. Never prints secrets."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path("website")
PROD = "https://website-eight-iota-ni22rhq9op.vercel.app"
LOCAL = "http://127.0.0.1:8765"

payload = {
    "name": "E2E QA Tejas",
    "phone": "7709099599",
    "email": "visitor.e2e.test@example.com",
    "city": "Kolhapur",
    "course": "CPC certification (AAPC)",
    "education": "B.Pharm",
    "message": "End-to-end QA — please confirm this enquiry arrived. Optional visitor email included.",
    "page": "E2E QA",
}


def post(base: str):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base + "/api/send-enquiry",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MedWiseE2E/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body[:300]}


def no_public_gmail():
    bad = []
    for f in list(ROOT.glob("*.html")) + [ROOT / "assets/js/site.js"]:
        text = f.read_text(encoding="utf-8")
        if "tejaswiulhalkar1996@gmail.com" in text.lower():
            bad.append(f.name)
        if re.search(r"[A-Za-z0-9._%+-]+@gmail\.com", text, re.I):
            bad.append(f.name + ":gmail-pattern")
    return bad


print("Public Gmail leak check:", "PASS" if not no_public_gmail() else "FAIL " + str(no_public_gmail()))

for label, base in (("LOCAL", LOCAL), ("PROD", PROD)):
    st, body = post(base)
    print(f"{label}: HTTP {st} body={body}")
    err = str(body.get("error", "")) + str(body.get("raw", ""))
    if "tejaswiulhalkar" in err.lower() or "@gmail.com" in err.lower():
        print(f"{label}: FAIL leaked destination email in API response")
    elif st == 200 and body.get("ok") is True:
        print(f"{label}: PASS enquiry accepted by API (delivery provider reported success)")
    else:
        print(f"{label}: FAIL / PENDING provider rejection (activation may be required)")
