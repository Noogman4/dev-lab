<?php

declare(strict_types=1);

namespace NetmonTest;

// These overrides exist only in an isolated, namespaced copy of the real library.
// No production fault flags or alternate persistence paths are introduced.
function netmon_test_temporary($stream): bool
{
    $metadata = \stream_get_meta_data($stream);
    return \strpos(\basename($metadata["uri"]), ".netmon-json-") === 0;
}

function fwrite($stream, string $data)
{
    static $writes = 0;
    if (netmon_test_temporary($stream)) {
        $writes++;
        switch ($GLOBALS["netmon_test_fault"] ?? "") {
            case "write-fail": return false;
            case "phantom-write": return \strlen($data);
            case "zero-write": return 0;
            case "partial-fail":
                return $writes === 1 ? \fwrite($stream, \substr($data, 0, 7)) : false;
            case "partial-success": return \fwrite($stream, \substr($data, 0, 7));
            case "slow-partial-success":
                \usleep(1000);
                return \fwrite($stream, \substr($data, 0, 7));
        }
    }
    return \fwrite($stream, $data);
}

function fflush($stream): bool
{
    if (($GLOBALS["netmon_test_fault"] ?? "") === "flush-fail" && netmon_test_temporary($stream)) {
        return false;
    }
    return \fflush($stream);
}

function fsync($stream): bool
{
    if (($GLOBALS["netmon_test_fault"] ?? "") === "sync-fail") {
        return false;
    }
    return \fsync($stream);
}

function fclose($stream): bool
{
    $fail = ($GLOBALS["netmon_test_fault"] ?? "") === "close-fail" && netmon_test_temporary($stream);
    $closed = \fclose($stream);
    return $closed && !$fail;
}

function rename(string $from, string $to): bool
{
    if (($GLOBALS["netmon_test_fault"] ?? "") === "rename-fail") {
        return false;
    }
    return \rename($from, $to);
}

function tempnam(string $directory, string $prefix)
{
    $fault = $GLOBALS["netmon_test_fault"] ?? "";
    if ($fault === "temp-fail") {
        return false;
    }
    if ($fault === "temp-fallback") {
        return \tempnam(\dirname($directory), $prefix);
    }
    $path = \tempnam($directory, $prefix);
    if ($fault === "temp-symlink" || $fault === "temp-dangling-symlink") {
        \unlink($path);
        \symlink($GLOBALS["netmon_test_victim"], $path);
    }
    return $path;
}

function flock($stream, int $operation): bool
{
    if (($GLOBALS["netmon_test_fault"] ?? "") === "lock-fail" && $operation !== LOCK_UN) {
        return false;
    }
    return \flock($stream, $operation);
}
