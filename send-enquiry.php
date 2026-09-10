<?php
/**
 * MedWise enquiry endpoint for Hostinger (PHP).
 * POST JSON → Gmail SMTP. Destination email never returned to browser.
 *
 * Requires mail-config.php in the same folder (copy from mail-config.example.php).
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  http_response_code(405);
  echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
  exit;
}

$configFile = __DIR__ . '/mail-config.php';
if (!is_file($configFile)) {
  http_response_code(500);
  echo json_encode([
    'ok' => false,
    'error' => 'Could not send. Please call or WhatsApp 77090 99599.'
  ]);
  exit;
}

$config = require $configFile;
$gmailUser = trim((string) ($config['GMAIL_USER'] ?? ''));
$gmailPass = trim((string) ($config['GMAIL_APP_PASSWORD'] ?? ''));
$toEmail = trim((string) ($config['FORM_TO_EMAIL'] ?? $gmailUser));

$raw = file_get_contents('php://input');
$data = json_decode($raw ?: '{}', true);
if (!is_array($data)) {
  $data = $_POST;
}

function field($data, $key) {
  if (!isset($data[$key])) return '';
  return trim((string) $data[$key]);
}

$name = field($data, 'name');
$phone = field($data, 'phone');
$visitorEmail = field($data, 'email');
$city = field($data, 'city');
$course = field($data, 'course');
$education = field($data, 'education');
$message = field($data, 'message');
$page = field($data, 'page');

if ($name === '' || $phone === '') {
  http_response_code(400);
  echo json_encode([
    'ok' => false,
    'error' => 'Please add your name and phone number so we can call you back.'
  ]);
  exit;
}

if ($toEmail === '' || $gmailUser === '' || $gmailPass === '') {
  http_response_code(500);
  echo json_encode([
    'ok' => false,
    'error' => 'Could not send. Please call or WhatsApp 77090 99599.'
  ]);
  exit;
}

$lines = [
  'New enquiry from the MedWise website',
  '',
  'Name: ' . $name,
  'Phone: ' . $phone,
];
if ($visitorEmail !== '') $lines[] = 'Visitor email: ' . $visitorEmail;
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
$lines[] = 'Sent: ' . gmdate('c');
$text = implode("\n", $lines);

$subject = 'New enquiry from MedWise website — ' . $name;
$replyTo = $visitorEmail !== '' ? $visitorEmail : $gmailUser;

try {
  medwise_smtp_send($gmailUser, $gmailPass, $toEmail, $subject, $text, $replyTo);
  echo json_encode(['ok' => true]);
} catch (Throwable $e) {
  error_log('MedWise send-enquiry failed: ' . $e->getMessage());
  http_response_code(502);
  echo json_encode([
    'ok' => false,
    'error' => 'Could not send. Please call or WhatsApp 77090 99599.'
  ]);
}

/**
 * Minimal Gmail SMTP (SSL 465) sender — no Composer required.
 */
function medwise_smtp_send($user, $pass, $to, $subject, $body, $replyTo) {
  $host = 'ssl://smtp.gmail.com';
  $port = 465;
  $errno = 0;
  $errstr = '';
  $fp = stream_socket_client($host . ':' . $port, $errno, $errstr, 30);
  if (!$fp) {
    throw new RuntimeException('SMTP connect failed');
  }
  stream_set_timeout($fp, 30);

  $expect = function ($codes) use ($fp) {
    $line = '';
    while ($str = fgets($fp, 515)) {
      $line .= $str;
      if (isset($str[3]) && $str[3] === ' ') break;
    }
    $code = (int) substr($line, 0, 3);
    if (!in_array($code, (array) $codes, true)) {
      throw new RuntimeException('SMTP unexpected: ' . trim($line));
    }
    return $line;
  };
  $cmd = function ($command, $codes) use ($fp, $expect) {
    fwrite($fp, $command . "\r\n");
    return $expect($codes);
  };

  $expect(220);
  $cmd('EHLO medwise.local', 250);
  $cmd('AUTH LOGIN', 334);
  $cmd(base64_encode($user), 334);
  $cmd(base64_encode($pass), 235);
  $cmd('MAIL FROM:<' . $user . '>', 250);
  $cmd('RCPT TO:<' . $to . '>', 250);
  $cmd('DATA', 354);

  $headers = [
    'From: MedWise Website <' . $user . '>',
    'To: <' . $to . '>',
    'Reply-To: <' . $replyTo . '>',
    'Subject: ' . medwise_encode_header($subject),
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
  ];
  $data = implode("\r\n", $headers) . "\r\n\r\n" . str_replace(["\r\n.", "\n."], ["\r\n..", "\n.."], $body);
  fwrite($fp, $data . "\r\n.\r\n");
  $expect(250);
  $cmd('QUIT', 221);
  fclose($fp);
}

function medwise_encode_header($text) {
  if (preg_match('/[^\x20-\x7E]/', $text)) {
    return '=?UTF-8?B?' . base64_encode($text) . '?=';
  }
  return $text;
}
