from playwright.sync_api import sync_playwright
import time

def test_form(url, label):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        # scroll to form
        form = page.locator("form[data-enquiry]").first
        form.scroll_into_view_if_needed()
        form.locator('input[name="name"]').fill("Browser E2E " + label)
        form.locator('input[name="phone"]').fill("7709099599")
        # city/course may be select
        if form.locator('select[name="city"]').count():
            form.locator('select[name="city"]').select_option(index=0)
        if form.locator('input[name="education"]').count():
            form.locator('input[name="education"]').fill("B.Pharm")
        if form.locator('select[name="course"]').count():
            form.locator('select[name="course"]').select_option(index=0)
        status = form.locator(".form-status")
        with page.expect_response(lambda r: "send-enquiry" in r.url and r.request.method == "POST", timeout=45000) as resp_info:
            form.locator('button[type="submit"]').click()
        resp = resp_info.value
        # wait for UI message
        page.wait_for_timeout(2500)
        text = status.inner_text()
        print(f"=== {label} ===")
        print("submit_url:", resp.url)
        print("submit_status:", resp.status)
        try:
            print("submit_body:", resp.text()[:200])
        except Exception as e:
            print("submit_body_err:", e)
        print("ui_status:", text)
        ok = resp.status == 200 and ("Thanks" in text or "received" in text.lower())
        print("RESULT:", "PASS" if ok else "FAIL")
        browser.close()
        return ok

results = []
results.append(test_form("http://127.0.0.1:8765/contact.html", "LOCAL_PORT_8765"))
results.append(test_form("https://website-eight-iota-ni22rhq9op.vercel.app/contact.html", "VERCEL"))
# Hostinger still old JS - expect FAIL until upload; still report
try:
    results.append(test_form("https://medwisehealthcaresolutions.com/contact", "HOSTINGER_COM"))
except Exception as e:
    print("=== HOSTINGER_COM ===")
    print("RESULT: FAIL", e)
    results.append(False)
print("SUMMARY", results, "all_pass_local_vercel=", all(results[:2]))
