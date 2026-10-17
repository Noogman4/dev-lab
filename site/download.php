<?php

declare(strict_types=1);

require __DIR__ . "/download-lib.php";

$config = netmon_download_config();
$downloads = (array) ($config["downloads"] ?? []);

$rawId = $_GET["id"] ?? "";
$downloadId = is_string($rawId) && strlen($rawId) <= 128 ? trim($rawId) : "";
$source = netmon_telemetry_text($_GET["src"] ?? "", 256);

if ($downloadId === "" || !isset($downloads[$downloadId]) || !is_array($downloads[$downloadId])) {
    http_response_code(404);
    header("Content-Type: text/plain; charset=utf-8");
    echo "Download not found.\n";
    exit;
}

$entry = $downloads[$downloadId];
$target = trim((string) ($entry["target"] ?? ""));
$label = trim((string) ($entry["label"] ?? $downloadId));

if ($target === "") {
    http_response_code(500);
    header("Content-Type: text/plain; charset=utf-8");
    echo "Download target is not configured.\n";
    exit;
}

$targetPath = __DIR__ . $target;
if (!is_file($targetPath)) {
    http_response_code(404);
    header("Content-Type: text/plain; charset=utf-8");
    echo "Requested file is currently not available.\n";
    exit;
}

netmon_record_download($config, $downloadId, $label, $target, $source);

$separator = (strpos($target, "?") === false) ? "?" : "&";
$redirectTarget = $target . $separator . "dl=1";

header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Pragma: no-cache");
header("Location: " . $redirectTarget, true, 302);
exit;
