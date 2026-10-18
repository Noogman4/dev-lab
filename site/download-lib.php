<?php

declare(strict_types=1);

// Hard ceilings, not request/config overrides. The source limits include one
// reserved overflow bucket; ordinary labels retain the M-01 UTF-8 byte limit.
const NETMON_STATS_SOURCE_BYTES = 256;
const NETMON_STATS_GLOBAL_SOURCES = 128;
const NETMON_STATS_FILE_SOURCES = 64;
const NETMON_STATS_OVERFLOW_SOURCE = "__other__";
const NETMON_STATS_MAX_FILES = 64;
const NETMON_STATS_MAX_DAYS = 3660;
const NETMON_STATS_MAX_EVENTS = 200;
const NETMON_JSON_MAX_BYTES = 4 * 1024 * 1024;
const NETMON_JSON_MAX_TOKENS = 65536;
const NETMON_JSON_MAX_DEPTH = 16;
const NETMON_JSON_LOCK_WAIT_MS = 1000;

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

function netmon_json_check_budget(string $raw): void
{
    $length = strlen($raw);
    if ($length > NETMON_JSON_MAX_BYTES) {
        throw new \RuntimeException("JSON storage byte budget exceeded.");
    }
    // Count structural punctuation before json_decode can allocate PHP arrays.
    // Quoted strings/escapes are skipped, so commas inside telemetry do not
    // consume the entry budget. json_decode remains the syntax validator.
    $offset = 0;
    $tokens = 0;
    $depth = 0;
    while ($offset < $length) {
        $offset += strcspn($raw, '"{}[],:', $offset);
        if ($offset >= $length) {
            break;
        }
        $character = $raw[$offset++];
        if ($character === '"') {
            while ($offset < $length) {
                $offset += strcspn($raw, "\"\\", $offset);
                if ($offset >= $length || $raw[$offset++] === '"') {
                    break;
                }
                $offset++; // Skip the one escaped character, including escaped quotes.
            }
            continue;
        }
        $tokens++;
        if ($character === "{" || $character === "[") {
            $depth++;
        } elseif ($character === "}" || $character === "]") {
            $depth--;
        }
        if ($tokens > NETMON_JSON_MAX_TOKENS || $depth > NETMON_JSON_MAX_DEPTH) {
            throw new \RuntimeException("JSON storage structure budget exceeded.");
        }
    }
}

function netmon_json_acquire_lock($handle, int $operation): bool
{
    $deadline = hrtime(true) + NETMON_JSON_LOCK_WAIT_MS * 1000000;
    do {
        if (@flock($handle, $operation | LOCK_NB)) {
            return true;
        }
        usleep(5000);
    } while (hrtime(true) < $deadline);
    return false;
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
            || !netmon_json_acquire_lock($lock, $operation)) {
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
    if ($info["size"] > NETMON_JSON_MAX_BYTES) {
        throw new \RuntimeException("JSON storage byte budget exceeded.");
    }
    $handle = @fopen($path, "rb");
    if ($handle === false) {
        throw new \RuntimeException("Cannot read JSON storage.");
    }
    try {
        $opened = fstat($handle);
        if (!netmon_json_same_file($info, $opened) || $opened["size"] > NETMON_JSON_MAX_BYTES) {
            throw new \RuntimeException("JSON storage changed while opening.");
        }
        $raw = stream_get_contents($handle, NETMON_JSON_MAX_BYTES + 1);
        if ($raw === false) {
            throw new \RuntimeException("Cannot read JSON storage.");
        }
    } finally {
        fclose($handle);
    }
    netmon_json_check_budget($raw);
    $decoded = json_decode($raw, true, NETMON_JSON_MAX_DEPTH, JSON_THROW_ON_ERROR);
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
        netmon_json_check_budget($encoded);
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

function netmon_stats_count($value): int
{
    if (!is_int($value) || $value < 0) {
        throw new \RuntimeException("Invalid statistics counter.");
    }
    return $value;
}

function netmon_stats_add(int $left, int $right): int
{
    // Saturation avoids float conversion / JSON overflow at PHP_INT_MAX.
    return $right > PHP_INT_MAX - $left ? PHP_INT_MAX : $left + $right;
}

function netmon_stats_add_source(array &$counts, string $source, int $amount, int $limit): void
{
    $ordinary = count($counts) - (array_key_exists(NETMON_STATS_OVERFLOW_SOURCE, $counts) ? 1 : 0);
    if ($source === "" || (!array_key_exists($source, $counts) && $ordinary >= $limit - 1)) {
        $source = NETMON_STATS_OVERFLOW_SOURCE;
    }
    $counts[$source] = netmon_stats_add($counts[$source] ?? 0, $amount);
}

function netmon_stats_sources(array $stored, int $limit): array
{
    $bounded = [];
    foreach ($stored as $source => $count) {
        $source = netmon_telemetry_text((string) $source, NETMON_STATS_SOURCE_BYTES);
        netmon_stats_add_source($bounded, $source, netmon_stats_count($count), $limit);
    }
    return $bounded;
}

function netmon_stats_days(array $days): array
{
    if (count($days) > NETMON_STATS_MAX_DAYS) {
        throw new \RuntimeException("Statistics day budget exceeded.");
    }
    foreach ($days as $day => $count) {
        if (!is_string($day) || preg_match('/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/D', $day) !== 1) {
            throw new \RuntimeException("Invalid statistics day.");
        }
        netmon_stats_count($count);
    }
    return $days;
}

function netmon_stats_add_day(array &$days, string $day): void
{
    if (!array_key_exists($day, $days) && count($days) >= NETMON_STATS_MAX_DAYS) {
        throw new \RuntimeException("Statistics day budget exceeded.");
    }
    $days[$day] = netmon_stats_add($days[$day] ?? 0, 1);
}

function netmon_prepare_stats(array $stored): array
{
    $stats = array_merge(netmon_default_stats(), $stored);
    foreach (["files", "sources", "days", "recent_events"] as $field) {
        if (!is_array($stats[$field])) {
            throw new \RuntimeException("Invalid statistics collection.");
        }
    }
    if (count($stats["files"]) > NETMON_STATS_MAX_FILES) {
        throw new \RuntimeException("Statistics file budget exceeded.");
    }
    $stats["total_downloads"] = netmon_stats_count($stats["total_downloads"]);
    $stats["updated_at"] = netmon_telemetry_text($stats["updated_at"], 64);
    $stats["sources"] = netmon_stats_sources($stats["sources"], NETMON_STATS_GLOBAL_SOURCES);
    $stats["days"] = netmon_stats_days($stats["days"]);
    foreach ($stats["files"] as $id => &$entry) {
        if (strlen((string) $id) > 128 || !is_array($entry)) {
            throw new \RuntimeException("Invalid statistics file entry.");
        }
        foreach (["sources", "days"] as $key) {
            if (array_key_exists($key, $entry) && !is_array($entry[$key])) {
                throw new \RuntimeException("Invalid statistics file collection.");
            }
        }
        $entry["count"] = netmon_stats_count(array_key_exists("count", $entry) ? $entry["count"] : 0);
        $entry["sources"] = netmon_stats_sources($entry["sources"] ?? [], NETMON_STATS_FILE_SOURCES);
        $entry["days"] = netmon_stats_days($entry["days"] ?? []);
        foreach (["label" => 256, "target" => 2048, "last_download_at" => 64] as $key => $limit) {
            if (array_key_exists($key, $entry)) {
                $entry[$key] = netmon_telemetry_text($entry[$key], $limit);
            }
        }
    }
    unset($entry);
    $stats["recent_events"] = array_slice($stats["recent_events"], 0, NETMON_STATS_MAX_EVENTS);
    foreach ($stats["recent_events"] as &$event) {
        if (!is_array($event)) {
            throw new \RuntimeException("Invalid statistics event.");
        }
        foreach (["timestamp" => 64, "day" => 10, "id" => 128, "label" => 256,
            "target" => 2048, "source" => NETMON_STATS_SOURCE_BYTES, "lang" => 8,
            "referrer" => 2048, "ip_hash" => 16] as $key => $limit) {
            if (array_key_exists($key, $event)) {
                $event[$key] = netmon_telemetry_text($event[$key], $limit);
            }
        }
    }
    unset($event);
    return $stats;
}

function netmon_load_stats(array $config, ?bool &$available = null): array
{
    $path = (string) ($config["stats_path"] ?? "");
    $stats = netmon_json_with_lock($path, LOCK_SH, static function (string $safePath): array {
        return netmon_prepare_stats(netmon_json_read($safePath, []));
    });
    $available = is_array($stats);
    return $available ? $stats : netmon_default_stats();
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

    if ($downloadId === "" || strlen($downloadId) > 128) {
        return false;
    }
    $source = netmon_telemetry_text($source, NETMON_STATS_SOURCE_BYTES);
    $label = netmon_telemetry_text($label, 256);
    $target = netmon_telemetry_text($target, 2048);
    return netmon_json_update($path, static function (array $stored) use ($config, $downloadId, $label, $target, $source): array {
        $stats = netmon_prepare_stats($stored);
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
        $stats["total_downloads"] = netmon_stats_add($stats["total_downloads"], 1);
        netmon_stats_add_day($stats["days"], $day);
        if ($source !== "") {
            netmon_stats_add_source($stats["sources"], $source, 1, NETMON_STATS_GLOBAL_SOURCES);
        }

        if (!isset($stats["files"][$downloadId]) || !is_array($stats["files"][$downloadId])) {
            if (count($stats["files"]) >= NETMON_STATS_MAX_FILES) {
                throw new \RuntimeException("Statistics file budget exceeded.");
            }
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
        $stats["files"][$downloadId]["count"] = netmon_stats_add($stats["files"][$downloadId]["count"], 1);
        $stats["files"][$downloadId]["last_download_at"] = $now;
        netmon_stats_add_day($stats["files"][$downloadId]["days"], $day);
        if ($source !== "") {
            netmon_stats_add_source($stats["files"][$downloadId]["sources"], $source, 1, NETMON_STATS_FILE_SOURCES);
        }

        $recentEvents = $stats["recent_events"];
        if (!is_array($recentEvents)) {
            $recentEvents = [];
        }
        array_unshift($recentEvents, $event);
        $maxEvents = min(NETMON_STATS_MAX_EVENTS, max(20, (int) ($config["max_recent_events"] ?? 200)));
        $stats["recent_events"] = array_slice($recentEvents, 0, $maxEvents);

        return $stats;
    }, netmon_default_stats());
}

function netmon_stats_token_valid($token): bool
{
    // RFC 6750 b64token, bounded before regex/comparison; no coercion or trim.
    return is_string($token) && strlen($token) >= 1 && strlen($token) <= 512
        && preg_match('/\A[A-Za-z0-9._~+\/-]+=*\z/D', $token) === 1;
}

function netmon_stats_authorization(): ?string
{
    $values = [];
    foreach (["HTTP_AUTHORIZATION", "REDIRECT_HTTP_AUTHORIZATION"] as $key) {
        if (array_key_exists($key, $_SERVER)) {
            $values[] = $_SERVER[$key];
        }
    }
    // Apache module and FPM may expose the header through different SAPI APIs.
    if (function_exists("getallheaders")) {
        $headers = getallheaders();
        if (!is_array($headers)) {
            return null;
        }
        foreach ($headers as $name => $value) {
            if (is_string($name) && strcasecmp($name, "Authorization") === 0) {
                $values[] = $value;
            }
        }
    }
    $authorization = null;
    foreach ($values as $value) {
        if (!is_string($value) || strlen($value) > 519
            || ($authorization !== null && $authorization !== $value)) {
            return null;
        }
        $authorization = $value;
    }
    if ($authorization === null
        || preg_match('/\ABearer ([A-Za-z0-9._~+\/-]+=*)\z/iD', $authorization, $match) !== 1
        || !netmon_stats_token_valid($match[1])) {
        return null;
    }
    return $match[1];
}

function netmon_require_stats_token(array $config): void
{
    // Also protect rejection responses; authenticate before any storage access.
    header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
    header("Pragma: no-cache");
    header("Expires: 0");
    header("Referrer-Policy: no-referrer");
    header("X-Content-Type-Options: nosniff");
    $token = $config["stats_token"] ?? null;
    if (!netmon_stats_token_valid($token)) {
        http_response_code(503);
        header("Content-Type: text/plain; charset=utf-8");
        echo "Statistics unavailable\n";
        exit;
    }
    $provided = netmon_stats_authorization();
    // URL tokens are intentionally unsupported, including arrays/conflicts.
    if (array_key_exists("token", $_GET) || $provided === null || !hash_equals($token, $provided)) {
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
