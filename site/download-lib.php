<?php

declare(strict_types=1);

function netmon_download_config(): array
{
    static $config = null;
    if ($config === null) {
        $config = require __DIR__ . "/download-config.php";
    }
    return $config;
}

function netmon_client_ip_hash(): string
{
    $ip = trim((string) ($_SERVER["REMOTE_ADDR"] ?? ""));
    if ($ip === "") {
        return "";
    }
    return substr(hash("sha256", $ip), 0, 16);
}

function netmon_guess_language(): string
{
    $lang = strtolower(trim((string) ($_GET["lang"] ?? "")));
    if ($lang !== "") {
        return substr($lang, 0, 8);
    }
    $accept = strtolower((string) ($_SERVER["HTTP_ACCEPT_LANGUAGE"] ?? ""));
    if (strpos($accept, "de") === 0) {
        return "de";
    }
    if (strpos($accept, "en") === 0) {
        return "en";
    }
    return "";
}

function netmon_default_stats(): array
{
    return [
        "updated_at" => "",
        "total_downloads" => 0,
        "files" => [],
        "sources" => [],
        "days" => [],
        "recent_events" => [],
    ];
}

function netmon_load_stats(array $config): array
{
    $path = (string) ($config["stats_path"] ?? "");
    if ($path === "" || !is_file($path)) {
        return netmon_default_stats();
    }

    $raw = @file_get_contents($path);
    if (!is_string($raw) || trim($raw) === "") {
        return netmon_default_stats();
    }

    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        return netmon_default_stats();
    }

    return array_merge(netmon_default_stats(), $decoded);
}

function netmon_record_download(
    array $config,
    string $downloadId,
    string $label,
    string $target,
    string $source
): bool {
    $path = (string) ($config["stats_path"] ?? "");
    if ($path === "") {
        return false;
    }

    $dir = dirname($path);
    if (!is_dir($dir) && !@mkdir($dir, 0775, true) && !is_dir($dir)) {
        return false;
    }

    $handle = @fopen($path, "c+");
    if ($handle === false) {
        return false;
    }

    $saved = false;
    try {
        if (!flock($handle, LOCK_EX)) {
            fclose($handle);
            return false;
        }

        $raw = stream_get_contents($handle);
        $stats = netmon_default_stats();
        if (is_string($raw) && trim($raw) !== "") {
            $decoded = json_decode($raw, true);
            if (is_array($decoded)) {
                $stats = array_merge($stats, $decoded);
            }
        }

        $now = gmdate("c");
        $day = gmdate("Y-m-d");
        $lang = netmon_guess_language();
        $referrer = trim((string) ($_SERVER["HTTP_REFERER"] ?? ""));
        $event = [
            "timestamp" => $now,
            "day" => $day,
            "id" => $downloadId,
            "label" => $label,
            "target" => $target,
            "source" => $source,
            "lang" => $lang,
            "referrer" => $referrer,
            "ip_hash" => netmon_client_ip_hash(),
        ];

        $stats["updated_at"] = $now;
        $stats["total_downloads"] = (int) ($stats["total_downloads"] ?? 0) + 1;
        $stats["days"][$day] = (int) ($stats["days"][$day] ?? 0) + 1;
        if ($source !== "") {
            $stats["sources"][$source] = (int) ($stats["sources"][$source] ?? 0) + 1;
        }

        if (!isset($stats["files"][$downloadId]) || !is_array($stats["files"][$downloadId])) {
            $stats["files"][$downloadId] = [
                "label" => $label,
                "target" => $target,
                "count" => 0,
                "last_download_at" => "",
                "sources" => [],
                "days" => [],
            ];
        }

        $stats["files"][$downloadId]["label"] = $label;
        $stats["files"][$downloadId]["target"] = $target;
        $stats["files"][$downloadId]["count"] = (int) ($stats["files"][$downloadId]["count"] ?? 0) + 1;
        $stats["files"][$downloadId]["last_download_at"] = $now;
        $stats["files"][$downloadId]["days"][$day] = (int) ($stats["files"][$downloadId]["days"][$day] ?? 0) + 1;
        if ($source !== "") {
            $stats["files"][$downloadId]["sources"][$source] = (int) ($stats["files"][$downloadId]["sources"][$source] ?? 0) + 1;
        }

        $recentEvents = $stats["recent_events"];
        if (!is_array($recentEvents)) {
            $recentEvents = [];
        }
        array_unshift($recentEvents, $event);
        $maxEvents = max(20, (int) ($config["max_recent_events"] ?? 200));
        $stats["recent_events"] = array_slice($recentEvents, 0, $maxEvents);

        rewind($handle);
        ftruncate($handle, 0);
        $saved = fwrite(
            $handle,
            json_encode($stats, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
        ) !== false;
        fflush($handle);
        flock($handle, LOCK_UN);
    } finally {
        fclose($handle);
    }

    return $saved;
}

function netmon_require_stats_token(array $config): void
{
    $token = trim((string) ($config["stats_token"] ?? ""));
    if ($token === "") {
        return;
    }

    $provided = trim((string) ($_GET["token"] ?? ""));
    if (!hash_equals($token, $provided)) {
        http_response_code(403);
        header("Content-Type: text/plain; charset=utf-8");
        echo "Forbidden\n";
        exit;
    }
}

function netmon_html(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, "UTF-8");
}
