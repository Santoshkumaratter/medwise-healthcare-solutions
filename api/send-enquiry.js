/**
 * MedWise enquiry API — Vercel Serverless
 * Sends form details to Tejas Gmail. Recipient is NEVER exposed to the browser.
 *
 * Env (Vercel → Settings → Environment Variables):
 *   FORM_TO_EMAIL         = destination Gmail
 *   GMAIL_USER            = same Gmail login
 *   GMAIL_APP_PASSWORD    = Google App Password (REQUIRED on Vercel)
 *
 * Transport:
 *   1) GMAIL_USER + GMAIL_APP_PASSWORD → Gmail SMTP (works on Vercel)
 *   2) Else FormSubmit (works locally; Cloudflare often blocks Vercel IPs)
 */
const nodemailer = require('nodemailer');

function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string' && req.body) {
    try {
      return JSON.parse(req.body);
    } catch (_) {
      return {};
    }
  }
  return {};
}

function field(data, key) {
  const v = data[key];
  return v == null ? '' : String(v).trim();
}

function buildText(fields) {
  const lines = [
    'New enquiry from the MedWise website',
    '',
    'Name: ' + fields.name,
    'Phone: ' + fields.phone
  ];
  if (fields.visitorEmail) lines.push('Visitor email: ' + fields.visitorEmail);
  if (fields.city) lines.push('City: ' + fields.city);
  if (fields.course) lines.push('Course: ' + fields.course);
  if (fields.education) lines.push('Qualification: ' + fields.education);
  if (fields.message) {
    lines.push('');
    lines.push('Message: ' + fields.message);
  }
  if (fields.page) {
    lines.push('');
    lines.push('Page: ' + fields.page);
  }
  lines.push('');
  lines.push('Sent: ' + new Date().toISOString());
  return lines.join('\n');
}

function clientError() {
  return {
    ok: false,
    error: 'Could not send. Please call or WhatsApp 77090 99599.'
  };
}

async function sendViaGmailSmtp(toEmail, gmailUser, gmailPass, fields, text) {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: { user: gmailUser, pass: gmailPass }
  });
  await transporter.sendMail({
    from: '"MedWise Website" <' + gmailUser + '>',
    to: toEmail,
    replyTo: fields.visitorEmail || gmailUser,
    subject: 'New enquiry from MedWise website — ' + fields.name,
    text: text
  });
}

async function sendViaFormSubmit(toEmail, fields, text) {
  const payload = {
    _subject: 'New enquiry from MedWise website — ' + fields.name,
    _template: 'table',
    _captcha: 'false',
    name: fields.name,
    phone: fields.phone,
    city: fields.city,
    course: fields.course,
    education: fields.education,
    message: fields.message,
    page: fields.page,
    details: text
  };
  if (fields.visitorEmail) payload.email = fields.visitorEmail;

  // Must match the URL Tejas activated on FormSubmit (alias, not deploy URL).
  const origin = (
    process.env.SITE_URL ||
    'https://website-eight-iota-ni22rhq9op.vercel.app'
  ).replace(/\/$/, '');

  const r = await fetch(
    'https://formsubmit.co/ajax/' + encodeURIComponent(toEmail),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Origin: origin,
        Referer: origin + '/contact.html',
        'User-Agent': 'MedWiseWebsite/1.0 (+vercel)'
      },
      body: JSON.stringify(payload)
    }
  );
  const raw = await r.text();
  let json = {};
  try {
    json = raw ? JSON.parse(raw) : {};
  } catch (_) {
    json = { parse_error: true, status: r.status, raw: String(raw).slice(0, 200) };
  }
  const success = json.success === true || json.success === 'true';
  if (!success) {
    const err = new Error('formsubmit_failed');
    err.formsubmit = Object.assign({ httpStatus: r.status }, json);
    throw err;
  }
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');

  if (req.method !== 'POST') {
    res.statusCode = 405;
    return res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }));
  }

  const data = readBody(req);
  const fields = {
    name: field(data, 'name'),
    phone: field(data, 'phone'),
    visitorEmail: field(data, 'email'),
    city: field(data, 'city'),
    course: field(data, 'course'),
    education: field(data, 'education'),
    message: field(data, 'message'),
    page: field(data, 'page')
  };

  if (!fields.name || !fields.phone) {
    res.statusCode = 400;
    return res.end(
      JSON.stringify({
        ok: false,
        error: 'Please add your name and phone number so we can call you back.'
      })
    );
  }

  const gmailUser = (process.env.GMAIL_USER || '').trim();
  const gmailPass = (process.env.GMAIL_APP_PASSWORD || '').trim();
  const toEmail = (process.env.FORM_TO_EMAIL || gmailUser).trim();

  if (!toEmail) {
    console.error('send-enquiry: FORM_TO_EMAIL / GMAIL_USER missing');
    res.statusCode = 500;
    return res.end(JSON.stringify(clientError()));
  }

  console.log(
    'send-enquiry transport:',
    gmailUser && gmailPass ? 'smtp' : 'formsubmit',
    'toLen=',
    toEmail.length
  );

  const text = buildText(fields);

  try {
    if (gmailUser && gmailPass) {
      await sendViaGmailSmtp(toEmail, gmailUser, gmailPass, fields, text);
    } else {
      await sendViaFormSubmit(toEmail, fields, text);
    }
    res.statusCode = 200;
    return res.end(JSON.stringify({ ok: true }));
  } catch (err) {
    const fsMsg =
      err && err.formsubmit
        ? JSON.stringify(err.formsubmit).slice(0, 500)
        : '';
    console.error(
      'send-enquiry failed:',
      err && err.message ? err.message : err,
      fsMsg || ''
    );
    res.statusCode = 502;
    return res.end(JSON.stringify(clientError()));
  }
};
