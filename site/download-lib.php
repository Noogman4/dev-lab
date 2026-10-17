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
    $ip = netmon_telemetry_text($_SERVER["REMOTE_ADDR"] ?? "", 128);
    if ($ip === "") {
        return "";
    }
    return substr(hash("sha256", $ip), 0, 16);
}

function netmon_guess_language(): string
{
    $lang = strtolower(netmon_telemetry_text($_GET["lang"] ?? "", 8));
    if ($lang !== "") {
        return $lang;
    }
    $accept = strtolower(netmon_telemetry_text($_SERVER["HTTP_ACCEPT_LANGUAGE"] ?? "", 256));
    if (strpos($accept, "de") === 0) {
        return "de";
    }
    if (strpos($accept, "en") === 0) {
        return "en";
    }
    return "";
}

function netmon_telemetry_text($value, int $maxBytes): string
{
    if (!is_string($value) || $maxBytes <= 0) {
        return "";
    }
    // Bound work before normalization; replacement characters may expand bytes.
    $value = json_decode(
        json_encode(substr($value, 0, $maxBytes), JSON_THROW_ON_ERROR | JSON_INVALID_UTF8_SUBSTITUTE),
        true,
        512,
        JSON_THROW_ON_ERROR
    );
    $value = substr($value, 0, $maxBytes);
    // The normalized input is valid UTF-8: only a cut final character can be invalid.
    while ($value !== "" && preg_match('//u', $value) !== 1) {
        $value = substr($value, 0, -1);
    }
    return trim($value);
}

function netmon_json_file_stat(string $path): ?array
{
    clearstatcache(true, $path);
    $info = @lstat($path);
    if ($info === false) {
        return null;
    }
    if (($info["mode"] & 0170000) !== 0100000 || $info["nlink"] !== 1) {
        throw new \RuntimeException("JSON storage requires a regular file with one link.");
    }
    return $info;
}

function netmon_json_same_file(array $left, array $right): bool
{
    return $left["dev"] === $right["dev"] && $left["ino"] === $right["ino"]
        && ($right["mode"] & 0170000) === 0100000 && $right["nlink"] === 1;
}

function netmon_json_storage_path(string $path): string
{
    // Only local absolute paths; refuse symlinks in every directory component.
    if ($path === "" || $path[0] !== "/" || strpos($path, "\0") !== false) {
        throw new \RuntimeException("Invalid JSON storage path.");
    }
    $parts = explode("/", $path);
    $name = array_pop($parts);
    if ($name === "" || $name === "." || $name === "..") {
        throw new \RuntimeException("Invalid JSON storage filename.");
    }
    $directory = "";
    foreach ($parts as $part) {
        if ($part === "" || $part === ".") {
            continue;
        }
        if ($part === "..") {
            throw new \RuntimeException("Parent traversal in JSON storage path.");
        }
        $directory .= "/" . $part;
        clearstatcache(true, $directory);
        $info = @lstat($directory);
        if ($info === false) {
            if (!@mkdir($directory, 0700) && !is_dir($directory)) {
                throw new \RuntimeException("Cannot create JSON storage directory.");
            }
            clearstatcache(true, $directory);
            $info = @lstat($directory);
        }
        if ($info === false || ($info["mode"] & 0170000) !== 0040000) {
            throw new \RuntimeException("Unsafe JSON storage directory.");
        }
    }
    $directory = $directory === "" ? "/" : $directory;
    $info = @lstat($directory);
    if ($info === false || ($info["mode"] & 0022) !== 0) {
        throw new \RuntimeException("JSON storage directory must not be group/world writable.");
    }
    return rtrim($directory, "/") . "/" . $name;
}

function netmon_json_with_lock(string $path, int $operation, callable $action)
{
    $lock = null;
    $locked = false;
    try {
        $path = netmon_json_storage_path($path);
        $lockPath = $path . ".lock";
        $info = netmon_json_file_stat($lockPath);
        if ($info === null) {
            $lock = @fopen($lockPath, "x+b");
            if (is_resource($lock)) {
                $info = netmon_json_file_stat($lockPath);
                if ($info === null || !netmon_json_same_file($info, fstat($lock))
                    || !@chmod($lockPath, 0600)) {
                    return false;
                }
            } else {
                // Another cooperating process may have created the stable lock.
                $info = netmon_json_file_stat($lockPath);
            }
        }
        if (!is_resource($lock)) {
            if ($info === null) {
                return false;
            }
            $lock = @fopen($lockPath, "r+b");
        }
        if (!is_resource($lock) || !netmon_json_same_file($info, fstat($lock))
            || !@flock($lock, $operation)) {
            return false;
        }
        $locked = true;
        $current = netmon_json_file_stat($lockPath);
        if ($current === null || !netmon_json_same_file($current, fstat($lock))
            || !@chmod($lockPath, $current["mode"] & 0600)) {
            return false;
        }
        return $action($path);
    } catch (\Throwable $error) {
        // Statistics failures must not break downloads or replace existing data.
        return false;
    } finally {
        if (is_resource($lock)) {
            if ($locked) {
                @flock($lock, LOCK_UN);
            }
            fclose($lock);
        }
        // Never unlink the mutex: rename replaces the data inode, not this lock.
    }
}

function netmon_json_read(string $path, array $default): array
{
    $info = netmon_json_file_stat($path);
    if ($info === null) {
        return $default;
    }
    $handle = @fopen($path, "rb");
    if ($handle === false) {
        throw new \RuntimeException("Cannot read JSON storage.");
    }
    try {
        if (!netmon_json_same_file($info, fstat($handle))) {
            throw new \RuntimeException("JSON storage changed while opening.");
        }
        $raw = stream_get_contents($handle);
        if ($raw === false) {
            throw new \RuntimeException("Cannot read JSON storage.");
        }
    } finally {
        fclose($handle);
    }
    $decoded = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($decoded)) {
        throw new \RuntimeException("JSON storage must contain an object or array.");
    }
    return $decoded;
}

function netmon_json_replace(string $path, string $encoded): bool
{
    $temporary = null;
    $handle = null;
    try {
        $existing = netmon_json_file_stat($path);
        // Never broaden existing owner permissions; drop group/world access.
        $mode = $existing === null ? 0600 : ($existing["mode"] & 0600);
        $directory = dirname($path);
        $temporary = @tempnam($directory, ".netmon-json-");
        if ($temporary === false) {
            return false;
        }
        if (dirname($temporary) !== $directory) {
            return false; // tempnam can otherwise fall back to the system temp dir.
        }
        $info = netmon_json_file_stat($temporary);
        // No truncating open: check the descriptor before the first write.
        $handle = @fopen($temporary, "r+b");
        if ($info === null || $info["size"] !== 0 || !is_resource($handle)
            || !netmon_json_same_file($info, fstat($handle))) {
            return false;
        }
        $offset = 0;
        $length = strlen($encoded);
        while ($offset < $length) {
            $written = @fwrite($handle, substr($encoded, $offset));
            if ($written === false || $written <= 0 || $written > $length - $offset) {
                return false;
            }
            $offset += $written;
        }
        if (!@chmod($temporary, $mode) || !@fflush($handle)
            || (function_exists("fsync") && !@fsync($handle))) {
            return false;
        }
        $closed = fclose($handle);
        $handle = null;
        if (!$closed) {
            return false;
        }
        $current = netmon_json_file_stat($temporary);
        if ($current === null || $current["size"] !== $length || !netmon_json_same_file($info, $current)) {
            return false;
        }
        $target = netmon_json_file_stat($path);
        if (($existing === null && $target !== null)
            || ($existing !== null && ($target === null || !netmon_json_same_file($existing, $target)))) {
            return false;
        }
        $renamed = @rename($temporary, $path);
        if ($renamed) {
            $temporary = null;
        }
        return $renamed;
    } finally {
        if (is_resource($handle)) {
            fclose($handle);
        }
        if (is_string($temporary)) {
            @unlink($temporary);
        }
    }
}

function netmon_json_update(string $path, callable $update, array $default = []): bool
{
    return netmon_json_with_lock($path, LOCK_EX, static function (string $safePath) use ($update, $default): bool {
        $next = $update(netmon_json_read($safePath, $default));
        if (!is_array($next)) {
            throw new \RuntimeException("JSON state updater must return an array.");
        }
        // Encode the complete state before creating/replacing any data file.
        $encoded = json_encode(
            $next,
            JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR | JSON_INVALID_UTF8_SUBSTITUTE
        );
        return netmon_json_replace($safePath, $encoded);
    }) === true;
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
    $stats = netmon_json_with_lock($path, LOCK_SH, static function (string $safePath): array {
        return array_merge(netmon_default_stats(), netmon_json_read($safePath, []));
    });
    return is_array($stats) ? $stats : netmon_default_stats();
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

    $source = netmon_telemetry_text($source, 256);
    return netmon_json_update($path, static function (array $stored) use ($config, $downloadId, $label, $target, $source): array {
        $stats = array_merge(netmon_default_stats(), $stored);
        $now = gmdate("c");
        $day = gmdate("Y-m-d");
        $lang = netmon_guess_language();
        $referrer = netmon_telemetry_text($_SERVER["HTTP_REFERER"] ?? "", 2048);
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

        return $stats;
    }, netmon_default_stats());
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
