<?php
// MarketSignalPro silent signup backend
// Upload this file next to index.html on GoDaddy PHP hosting.
// Submissions are emailed to support@marketsignalpro.com and saved to signups.csv.

header('Content-Type: application/json');

$recipient = "support@marketsignalpro.com";
$siteName  = "MarketSignalPro";
$csvFile   = __DIR__ . "/signups.csv";

function respond($ok, $message, $status = 200) {
    http_response_code($status);
    echo json_encode(["ok" => $ok, "message" => $message]);
    exit;
}

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    respond(false, "Invalid request method.", 405);
}

// Honeypot spam field. Real visitors never fill this.
if (!empty($_POST["company"] ?? "")) {
    respond(true, "Thanks.");
}

$name  = trim($_POST["name"] ?? "");
$email = trim($_POST["email"] ?? "");

if ($name === "" || $email === "") {
    respond(false, "Please enter your name and email.", 400);
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(false, "Please enter a valid email address.", 400);
}

$nameSafe  = preg_replace('/[\r\n]+/', ' ', $name);
$emailSafe = preg_replace('/[\r\n]+/', ' ', $email);
$ip        = $_SERVER["REMOTE_ADDR"] ?? "";
$userAgent = $_SERVER["HTTP_USER_AGENT"] ?? "";
$page      = $_SERVER["HTTP_REFERER"] ?? "";
$time      = date("Y-m-d H:i:s");

// Save to CSV
$isNewFile = !file_exists($csvFile);
$fp = fopen($csvFile, "a");
if ($fp) {
    if ($isNewFile) {
        fputcsv($fp, ["timestamp", "name", "email", "ip", "user_agent", "page"]);
    }
    fputcsv($fp, [$time, $nameSafe, $emailSafe, $ip, $userAgent, $page]);
    fclose($fp);
}

// Email notification
$subject = "New MarketSignalPro early-access signup";
$body =
"New early-access signup\n\n" .
"Name: {$nameSafe}\n" .
"Email: {$emailSafe}\n" .
"Time: {$time}\n" .
"IP: {$ip}\n" .
"Page: {$page}\n";

$headers = [];
$headers[] = "From: MarketSignalPro <support@marketsignalpro.com>";
$headers[] = "Reply-To: {$nameSafe} <{$emailSafe}>";
$headers[] = "Content-Type: text/plain; charset=UTF-8";

$mailSent = @mail($recipient, $subject, $body, implode("\r\n", $headers));

// Even if mail() is disabled, the signup is still saved to CSV.
if (!$mailSent) {
    respond(true, "Signup saved. Email notification may need GoDaddy mail configuration.");
}

respond(true, "Signup received.");
?>
