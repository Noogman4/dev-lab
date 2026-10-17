<?php

declare(strict_types=1);

// CLI-only harness. The Python tests copy this and the subject into a temp dir.
$payload = json_decode(base64_decode($argv[1], true), true, 512, JSON_THROW_ON_ERROR);
require __DIR__ . "/" . ($payload["library"] ?? "download-lib.php");
$prefix = $payload["namespace"] ?? "";
$GLOBALS["netmon_test_fault"] = $payload["fault"] ?? "";
$GLOBALS["netmon_test_victim"] = $payload["victim"] ?? "";
$_GET = ["lang" => base64_decode($payload["lang"] ?? "", true)];
$_SERVER["HTTP_REFERER"] = base64_decode($payload["referrer"] ?? "", true);
$_SERVER["HTTP_ACCEPT_LANGUAGE"] = base64_decode($payload["accept"] ?? "", true);
$_SERVER["REMOTE_ADDR"] = base64_decode($payload["remote_addr"] ?? base64_encode("127.0.0.1"), true);
$config = ["stats_path" => $payload["path"], "max_recent_events" => $payload["max_events"] ?? 200];
$record = $prefix . "netmon_record_download";
$load = $prefix . "netmon_load_stats";
$update = $prefix . "netmon_json_update";
$ready = $payload["start"] ?? "";
if ($ready !== "") {
    while (!is_file($ready)) {
        usleep(1000);
        clearstatcache(true, $ready);
    }
}

$saved = true;
switch ($payload["action"] ?? "record") {
    case "serialize-error":
        $saved = $update($payload["path"], static function (array $stats): array {
            $stats["non_finite"] = INF;
            return $stats;
        });
        break;
    case "invalid-state":
        $saved = $update($payload["path"], static function (array $stats) {
            return "not a state object";
        });
        break;
    case "read":
        break;
    default:
        for ($index = 0; $index < ($payload["iterations"] ?? 1); $index++) {
            $result = $record(
                $config,
                "artifact",
                "Test artifact",
                "/artifact.bin",
                base64_decode($payload["source"] ?? "", true)
            );
            $saved = $result && $saved;
        }
}
echo json_encode(["saved" => $saved, "stats" => $load($config)], JSON_THROW_ON_ERROR);
