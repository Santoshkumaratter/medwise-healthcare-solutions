# -*- coding: utf-8 -*-
"""Build multi-page MedWise site from interactive preview HTML."""
import base64
import os
import re
from pathlib import Path

SRC = Path(r"c:\Users\santo\OneDrive\Documents\Tejas\medwise-website-PREVIEW (1).html")
OUT = Path(r"c:\Users\santo\OneDrive\Documents\Tejas\website")

PAGES = {
    "home": {
        "file": "index.html",
        "title": "Best Medical Coding Class in Kolhapur | CPC & CCS Training",
        "description": "The best medical coding class in Kolhapur. AAPC CPC and AHIMA CCS certification training for Kolhapur, Sangli, Satara and Belgaum students. 100% placement.",
        "canonical": "https://www.medwisehealthcaresolutions.in/",
        "nav": "home",
        "apply_id": "home-apply",
    },
    "about": {
        "file": "about.html",
        "title": "About MedWise — Medical Coding Institute in Kolhapur",
        "description": "MedWise is Kolhapur's specialist medical coding institute in Rajarampuri: practising certified coders as faculty, batches of 20, and full placement support.",
        "canonical": "https://www.medwisehealthcaresolutions.in/about.html",
        "nav": "about",
        "apply_id": "about-apply",
    },
    "courses": {
        "file": "courses.html",
        "title": "CPC & CCS Medical Coding Courses in Kolhapur | MedWise",
        "description": "Full CPC (AAPC) and CCS (AHIMA) syllabus, batch timings and fee structure at Kolhapur's specialist medical coding institute. 100% placement guarantee.",
        "canonical": "https://www.medwisehealthcaresolutions.in/courses.html",
        "nav": "courses",
        "apply_id": "courses-apply",
    },
    "contact": {
        "file": "contact.html",
        "title": "Contact MedWise | Medical Coding Class in Kolhapur",
        "description": "Visit MedWise at Yashodhara Apartment, Rajarampuri 6th Lane, Kolhapur 416008. Call or WhatsApp 7709099599 to book a free medical coding demo class.",
        "canonical": "https://www.medwisehealthcaresolutions.in/contact.html",
        "nav": "contact",
        "apply_id": "apply",
    },
    "kolhapur": {
        "file": "medical-coding-classes-in-kolhapur.html",
        "title": "Medical Coding Classes in Kolhapur — Batches & Fees",
        "description": "Medical coding classes in Kolhapur at Rajarampuri 6th Lane. Weekday, evening and weekend CPC and CCS batches of 20 students, with 100% placement guarantee.",
        "canonical": "https://www.medwisehealthcaresolutions.in/medical-coding-classes-in-kolhapur.html",
        "nav": None,
        "apply_id": "kolhapur-apply",
    },
    "sangli": {
        "file": "medical-coding-classes-in-sangli.html",
        "title": "Medical Coding Classes in Sangli & Miraj | MedWise",
        "description": "Medical coding classes for Sangli, Miraj and Ichalkaranji students — weekend classroom batches in Kolhapur or live online CPC and CCS training with placement.",
        "canonical": "https://www.medwisehealthcaresolutions.in/medical-coding-classes-in-sangli.html",
        "nav": None,
        "apply_id": "sangli-apply",
    },
    "satara": {
        "file": "medical-coding-classes-in-satara.html",
        "title": "Medical Coding Classes in Satara & Karad | MedWise",
        "description": "Medical coding classes for Satara and Karad students. Live online CPC and CCS certification training from Kolhapur's specialist institute, with placement.",
        "canonical": "https://www.medwisehealthcaresolutions.in/medical-coding-classes-in-satara.html",
        "nav": None,
        "apply_id": "satara-apply",
    },
    "belgaum": {
        "file": "medical-coding-classes-in-belgaum.html",
        "title": "Medical Coding Classes in Belgaum (Belagavi) | MedWise",
        "description": "Medical coding classes for Belgaum, Belagavi, Nipani and Chikodi students. CPC and CCS training online or in weekend Kolhapur batches, with placement support.",
        "canonical": "https://www.medwisehealthcaresolutions.in/medical-coding-classes-in-belgaum.html",
        "nav": None,
        "apply_id": "belgaum-apply",
    },
}

HREF_MAP = {
    "home": "index.html",
    "about": "about.html",
    "courses": "courses.html",
    "contact": "contact.html",
    "kolhapur": "medical-coding-classes-in-kolhapur.html",
    "sangli": "medical-coding-classes-in-sangli.html",
    "satara": "medical-coding-classes-in-satara.html",
    "belgaum": "medical-coding-classes-in-belgaum.html",
}


def main():
    html = SRC.read_text(encoding="utf-8")

    # Extract CSS (between first <style> and </style>)
    css_m = re.search(r"<style>(.*?)</style>", html, re.S)
    if not css_m:
        raise SystemExit("CSS not found")
    css = css_m.group(1)
    # Drop preview-bar styles (optional keep harmless)
    css = re.sub(r"\.preview-bar\s*\{[^}]*\}", "", css)

    # Extract logo from first brand img
    logo_m = re.search(
        r'<img src="data:image/png;base64,([^"]+)" alt="MedWise Healthcare Solutions[^"]*"',
        html,
    )
    if not logo_m:
        raise SystemExit("Logo not found")
    logo_b64 = logo_m.group(1)

    (OUT / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "img").mkdir(parents=True, exist_ok=True)

    (OUT / "assets" / "css" / "style.css").write_text(css, encoding="utf-8")
    (OUT / "assets" / "img" / "logo.png").write_bytes(base64.b64decode(logo_b64))

    # Extract footer
    foot_m = re.search(r'<footer class="foot">(.*?)</footer>', html, re.S)
    if not foot_m:
        raise SystemExit("Footer not found")
    footer_inner = foot_m.group(1)

    # Extract float buttons
    float_m = re.search(r'<div class="float">(.*?)</div>\s*<script>', html, re.S)
    if not float_m:
        raise SystemExit("Float bar not found")
    float_html = '<div class="float">' + float_m.group(1) + "</div>"

    # Extract each page body
    page_bodies = {}
    for slug in PAGES:
        m = re.search(
            rf'<div class="pg" id="pg-{slug}" data-page="{slug}"[^>]*>(.*?)</div>\s*(?=<div class="pg"|<footer)',
            html,
            re.S,
        )
        if not m:
            raise SystemExit(f"Page not found: {slug}")
        body = m.group(1).strip()
        # Fix main id for skip link consistency
        body = re.sub(r"<main[^>]*>", '<main id="main">', body, count=1)
        body = body.replace('id="courses-cpc"', 'id="cpc"')
        body = body.replace('id="courses-ccs"', 'id="ccs"')
        body = body.replace('id="contact-apply"', 'id="apply"')
        page_bodies[slug] = body

    # Shared JS
    js = r"""(function () {
  'use strict';

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? 'Close' : 'Menu';
    });

    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.innerWidth <= 820) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'Menu';
      }
    });
  }

  /* Enquiry forms → FormSubmit (Vercel-compatible, no PHP).
     Deliveries go to info@medwisehealthcaresolutions.in */
  var ENQUIRY_ENDPOINT = 'https://formsubmit.co/ajax/info@medwisehealthcaresolutions.in';
  var forms = document.querySelectorAll('form[data-enquiry]');

  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var status = form.querySelector('.form-status');
      var btn = form.querySelector('button[type="submit"]');
      var get = function (n) {
        var el = form.elements[n];
        return el ? String(el.value).trim() : '';
      };

      var name = get('name');
      var phone = get('phone');

      if (!name || !phone) {
        if (status) {
          status.style.color = '#C0392B';
          status.textContent = 'Please add your name and phone number so we can call you back.';
        }
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Sending…';
      }
      if (status) {
        status.style.color = '';
        status.textContent = 'Sending your enquiry…';
      }

      var payload = {
        _subject: 'New enquiry from MedWise website — ' + name,
        _template: 'table',
        _captcha: 'false',
        name: name,
        phone: phone,
        email: get('email') || 'no-reply@medwisehealthcaresolutions.in',
        city: get('city'),
        course: get('course'),
        education: get('education'),
        message: get('message'),
        page: document.title || location.pathname
      };

      fetch(ENQUIRY_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (json) {
            return { ok: res.ok, json: json };
          });
        })
        .then(function (result) {
          var success = result.ok || (result.json && (result.json.success === 'true' || result.json.success === true));
          if (success) {
            if (status) {
              status.style.color = '';
              status.textContent = 'Thanks, ' + name.split(' ')[0] + '. We received your enquiry and will call you back the same working day.';
            }
            form.reset();
          } else {
            var msg = (result.json && result.json.message) ? result.json.message : 'Could not send. Please call or WhatsApp 77090 99599.';
            if (status) {
              status.style.color = '#C0392B';
              status.textContent = msg;
            }
          }
        })
        .catch(function () {
          if (status) {
            status.style.color = '#C0392B';
            status.textContent = 'Could not send. Please call or WhatsApp 77090 99599.';
          }
        })
        .finally(function () {
          if (btn) {
            btn.disabled = false;
            btn.textContent = 'Send my enquiry';
          }
        });
    });
  });

  var counters = document.querySelectorAll('[data-count]');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (counters.length && 'IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var target = parseInt(el.getAttribute('data-count'), 10);
        var suffix = el.getAttribute('data-suffix') || '';
        var start = null;

        function tick(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / 1100, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        io.unobserve(el);
      });
    }, { threshold: 0.4 });

    Array.prototype.forEach.call(counters, function (c) { io.observe(c); });
  } else {
    Array.prototype.forEach.call(counters, function (c) {
      c.textContent = c.getAttribute('data-count') + (c.getAttribute('data-suffix') || '');
    });
  }

  var y = document.querySelectorAll('[data-year]');
  Array.prototype.forEach.call(y, function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
"""
    (OUT / "assets" / "js" / "site.js").write_text(js, encoding="utf-8")

    def fix_links(chunk, current_slug, apply_id):
        def fix_any(m):
            full = m.group(0)
            slug_m = re.search(r'data-go="(\w+)"', full)
            if not slug_m:
                return full
            slug = slug_m.group(1)
            href = HREF_MAP.get(slug, "index.html")
            if 'href="' in full:
                full = re.sub(r'href="[^"]*"', f'href="{href}"', full, count=1)
            else:
                full = full.replace("<a ", f'<a href="{href}" ', 1)
            full = re.sub(r'\s*data-go="[^"]*"', "", full)
            return full

        chunk = re.sub(r"<a\b[^>]*data-go=\"\w+\"[^>]*>", fix_any, chunk)

        # Replace embedded logo data URIs with file path
        chunk = re.sub(
            r'src="data:image/png;base64,[A-Za-z0-9+/=]+"',
            'src="assets/img/logo.png"',
            chunk,
        )

        chunk = chunk.replace('href="#apply"', f'href="#{apply_id}"')

        chunk = chunk.replace(
            "Opens WhatsApp with your details filled in. We reply the same working day.",
            "We will email your enquiry to MedWise and call you back the same working day.",
        )
        chunk = chunk.replace(
            "Opens WhatsApp with your details filled in.",
            "We will email your enquiry to MedWise and call you back the same working day.",
        )

        chunk = chunk.replace(
            'href="https://www.instagram.com/medwisehealthcaresolutions/" rel="noopener"',
            'href="https://www.instagram.com/medwisehealthcaresolutions/" target="_blank" rel="noopener"',
        )
        chunk = chunk.replace(
            'href="https://wa.me/917709099599" rel="noopener"',
            'href="https://wa.me/917709099599" target="_blank" rel="noopener"',
        )

        return chunk

    # Build utility + header template pieces from source
    util_m = re.search(r'<div class="utility">.*?</div>\s*</div>', html, re.S)
    utility = util_m.group(0) if util_m else ""

    head_m = re.search(r'<header class="masthead">.*?</header>', html, re.S)
    header = head_m.group(0) if head_m else ""
    # Fix brand href and logo in header once
    header = re.sub(
        r'<a class="brand" href="#" data-go="home"',
        '<a class="brand" href="index.html"',
        header,
    )
    header = re.sub(
        r'src="data:image/png;base64,[A-Za-z0-9+/=]+"',
        'src="assets/img/logo.png"',
        header,
        count=1,
    )
    # Nav links
    header = re.sub(
        r'<a href="#" data-go="home"([^>]*)>Home</a>',
        r'<a href="index.html"\1>Home</a>',
        header,
    )
    header = re.sub(
        r'<a href="#" data-go="about"([^>]*)>About us</a>',
        r'<a href="about.html"\1>About us</a>',
        header,
    )
    header = re.sub(
        r'<a href="#" data-go="courses"([^>]*)>What we offer</a>',
        r'<a href="courses.html"\1>What we offer</a>',
        header,
    )
    header = re.sub(
        r'<a href="#" data-go="contact"([^>]*)>Contact us</a>',
        r'<a href="contact.html"\1>Contact us</a>',
        header,
    )

    footer = "<footer class=\"foot\">" + footer_inner + "</footer>"
    footer = fix_links(footer, "home", "home-apply")
    float_html = fix_links(float_html, "home", "home-apply")

    php = r"""<?php
/**
 * MedWise enquiry form handler
 * Edit TO_EMAIL below to the inbox that should receive enquiries.
 */
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

function field($key) {
    return isset($_POST[$key]) ? trim((string)$_POST[$key]) : '';
}

$name = field('name');
$phone = field('phone');
$email = field('email');
$city = field('city');
$course = field('course');
$education = field('education');
$message = field('message');
$page = field('page');

if ($name === '' || $phone === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Name and phone are required.']);
    exit;
}

// ---- Configure recipient email here ----
$TO_EMAIL = 'info@medwisehealthcaresolutions.in';
$FROM_EMAIL = 'noreply@medwisehealthcaresolutions.in';
$FROM_NAME = 'MedWise Website';

$subject = 'New enquiry from MedWise website — ' . $name;

$lines = [
    'New enquiry from the MedWise website',
    '',
    'Name: ' . $name,
    'Phone: ' . $phone,
];
if ($email !== '') $lines[] = 'Email: ' . $email;
if ($city !== '') $lines[] = 'City: ' . $city;
if ($course !== '') $lines[] = 'Course: ' . $course;
if ($education !== '') $lines[] = 'Qualification: ' . $education;
if ($message !== '') {
    $lines[] = '';
    $lines[] = 'Message: ' . $message;
}
if ($page !== '') {
    $lines[] = '';
    $lines[] = 'Page: ' . $page;
}
$lines[] = '';
$lines[] = 'Sent: ' . date('Y-m-d H:i:s');

$body = implode("\n", $lines);

$headers = [];
$headers[] = 'MIME-Version: 1.0';
$headers[] = 'Content-Type: text/plain; charset=UTF-8';
$headers[] = 'From: ' . $FROM_NAME . ' <' . $FROM_EMAIL . '>';
$headers[] = 'Reply-To: ' . ($email !== '' ? $email : $TO_EMAIL);
$headers[] = 'X-Mailer: MedWise-Website';

$ok = @mail($TO_EMAIL, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers));

if (!$ok) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Mail server could not send. Please call or WhatsApp 77090 99599.']);
    exit;
}

echo json_encode(['ok' => true]);
"""
    (OUT / "send-enquiry.php").write_text(php, encoding="utf-8")

    # .htaccess for HTTPS optional + index
    htaccess = """DirectoryIndex index.html index.php
Options -Indexes
"""
    (OUT / ".htaccess").write_text(htaccess, encoding="utf-8")

    for slug, meta in PAGES.items():
        body = fix_links(page_bodies[slug], slug, meta["apply_id"])

        # Per-page header with aria-current on nav item only (not brand)
        page_header = header
        page_header = re.sub(r'\s*aria-current="page"', "", page_header)
        if meta["nav"]:
            nav_labels = {
                "home": ("index.html", "Home"),
                "about": ("about.html", "About us"),
                "courses": ("courses.html", "What we offer"),
                "contact": ("contact.html", "Contact us"),
            }
            href, label = nav_labels[meta["nav"]]
            page_header = page_header.replace(
                f'<a href="{href}">{label}</a>',
                f'<a href="{href}" aria-current="page">{label}</a>',
                1,
            )
        page_header = re.sub(
            r'(class="btn btn-green btn-sm" href=")[^"]*(")',
            rf'\1#{meta["apply_id"]}\2',
            page_header,
        )

        page_html = f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta['title']}</title>
<meta name="description" content="{meta['description']}">
<link rel="canonical" href="{meta['canonical']}">
<meta property="og:title" content="{meta['title']}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:url" content="{meta['canonical']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="MedWise Healthcare Solutions">
<link rel="icon" href="assets/img/logo.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
{utility}
{page_header}
{body}
{footer}
{float_html}
<script src="assets/js/site.js" defer></script>
</body>
</html>
"""
        (OUT / meta["file"]).write_text(page_html, encoding="utf-8")
        print("Wrote", meta["file"])

    print("Done. Output:", OUT)


if __name__ == "__main__":
    main()
