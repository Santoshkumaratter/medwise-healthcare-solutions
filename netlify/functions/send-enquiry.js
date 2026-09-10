/**
 * Netlify Function — MedWise enquiry mailer
 * Env (Netlify → Site settings → Environment variables):
 *   FORM_TO_EMAIL, GMAIL_USER, GMAIL_APP_PASSWORD
 */
const nodemailer = require('nodemailer');

const ALLOWED_ORIGINS = [
  'https://medwisehealthcaresolutions.com',
  'https://www.medwisehealthcaresolutions.com',
  'http://127.0.0.1:8765',
  'http://localhost:8765',
  'http://127.0.0.1:8888',
  'http://localhost:8888'
];

function corsHeaders(origin) {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Accept'
  };
  let allow = ALLOWED_ORIGINS.indexOf(origin) !== -1;
  if (!allow && origin) {
    try {
      const host = new URL(origin).hostname;
      allow =
        host === 'localhost' ||
        host === '127.0.0.1' ||
        host.endsWith('.netlify.app');
    } catch (_) {
      allow = false;
    }
  }
  if (allow) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Vary'] = 'Origin';
  }
  return headers;
}

function field(data, key) {
  const v = data[key];
  return v == null ? '' : String(v).trim();
}

function clientError() {
  return {
    ok: false,
    error: 'Could not send. Please call or WhatsApp 77090 99599.'
  };
}

exports.handler = async function handler(event) {
  const origin = String(
    (event.headers && (event.headers.origin || event.headers.Origin)) || ''
  );
  const headers = corsHeaders(origin);

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ ok: false, error: 'Method not allowed' })
    };
  }

  let data = {};
  try {
    const raw = event.body
      ? event.isBase64Encoded
        ? Buffer.from(event.body, 'base64').toString('utf8')
        : event.body
      : '{}';
    data = typeof raw === 'string' ? JSON.parse(raw || '{}') : raw || {};
  } catch (_) {
    data = {};
  }

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
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({
        ok: false,
        error: 'Please add your name and phone number so we can call you back.'
      })
    };
  }

  const gmailUser = (process.env.GMAIL_USER || '').trim();
  const gmailPass = (process.env.GMAIL_APP_PASSWORD || '').trim();
  const toEmail = (process.env.FORM_TO_EMAIL || gmailUser).trim();

  if (!toEmail || !gmailUser || !gmailPass) {
    console.error('send-enquiry: missing GMAIL_USER / GMAIL_APP_PASSWORD / FORM_TO_EMAIL');
    return { statusCode: 500, headers, body: JSON.stringify(clientError()) };
  }

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

  try {
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: { user: gmailUser, pass: gmailPass }
    });

    // Respond immediately so the UI feels instant (<1 s).
    // Email is sent in the background after we reply.
    const response = { statusCode: 200, headers, body: JSON.stringify({ ok: true }) };

    // Background send — errors only logged, not shown to visitor.
    transporter.sendMail({
      from: '"MedWise Website" <' + gmailUser + '>',
      to: toEmail,
      replyTo: fields.visitorEmail || gmailUser,
      subject: 'New enquiry from MedWise website — ' + fields.name,
      text: lines.join('\n')
    }).catch(function (err) {
      console.error('send-enquiry mail failed:', err && err.message ? err.message : err);
    });

    return response;
  } catch (err) {
    console.error('send-enquiry failed:', err && err.message ? err.message : err);
    return { statusCode: 502, headers, body: JSON.stringify(clientError()) };
  }
};
