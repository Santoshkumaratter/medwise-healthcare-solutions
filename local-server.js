/**
 * Local API + static server for form testing (mirrors Vercel /api/send-enquiry).
 * Usage: node local-server.js
 * Reads .env.local / .env if present.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

function loadEnvFile(file) {
  const p = path.join(__dirname, file);
  if (!fs.existsSync(p)) return;
  fs.readFileSync(p, 'utf8').split(/\r?\n/).forEach((line) => {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!m) return;
    let v = m[2].trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    if (!process.env[m[1]]) process.env[m[1]] = v;
  });
}

loadEnvFile('.env.local');
loadEnvFile('.env');

const handler = require('./api/send-enquiry.js');
const ROOT = __dirname;
const PORT = process.env.PORT || 8765;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.json': 'application/json'
};

function sendFile(res, filePath) {
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://127.0.0.1:' + PORT);

  if (u.pathname === '/api/send-enquiry' || u.pathname === '/send-enquiry.php') {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
      if (raw.length > 1e6) req.destroy();
    });
    req.on('end', async () => {
      try {
        req.body = raw ? JSON.parse(raw) : {};
      } catch (_) {
        req.body = {};
      }
      const fakeRes = {
        statusCode: 200,
        headers: {},
        setHeader(k, v) {
          this.headers[k] = v;
        },
        end(body) {
          res.writeHead(this.statusCode, this.headers);
          res.end(body);
        }
      };
      await handler(req, fakeRes);
    });
    return;
  }

  let pathname = decodeURIComponent(u.pathname);
  if (pathname === '/') pathname = '/index.html';
  const filePath = path.normalize(path.join(ROOT, pathname.replace(/^\/+/, '')));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
  sendFile(res, filePath);
});

server.listen(PORT, '127.0.0.1', () => {
  const smtp = !!(process.env.GMAIL_USER && process.env.GMAIL_APP_PASSWORD);
  const dest = process.env.FORM_TO_EMAIL || process.env.GMAIL_USER || '';
  console.log('MedWise local server http://127.0.0.1:' + PORT);
  if (smtp) {
    console.log('Mail: Gmail SMTP as', process.env.GMAIL_USER);
  } else if (dest) {
    console.log('Mail: FormSubmit → destination set (App Password not set)');
  } else {
    console.log('Mail: NO — set FORM_TO_EMAIL in .env.local');
  }
});
