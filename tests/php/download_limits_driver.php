<?php

declare(strict_types=1);

namespace NetmonTest {
    // Instrument only the isolated namespaced library, never production code.
    function json_decode(string $json, bool $associative = false, int $depth = 512, int $flags = 0)
    {
        $GLOBALS["limit_decodes"]++;
        return \json_decode($json, $associative, $depth, $flags);
    }

    function stream_get_contents($stream, int $length = -1, int $offset = -1)
    {
        $GLOBALS["limit_reads"][] = $length;
        if (($GLOBALS["limits_fault"] ?? "") === "grow-on-read") {
            $path = \stream_get_meta_data($stream)["uri"];
            \file_put_contents($path, \str_repeat(" ", NETMON_JSON_MAX_BYTES + 1), FILE_APPEND);
        }
        return \stream_get_contents($stream, $length, $offset);
    }
}

namespace {
    $payload = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
    $GLOBALS["netmon_test_fault"] = $payload["fault"] ?? "";
    $GLOBALS["limits_fault"] = $payload["fault"] ?? "";
    $GLOBALS["limit_decodes"] = 0;
    $GLOBALS["limit_reads"] = [];
    require __DIR__ . "/" . (!empty($payload["instrument"]) || !empty($payload["fault"]) ? "fault-library.php" : "download-lib.php");
    $prefix = !empty($payload["instrument"]) || !empty($payload["fault"]) ? "NetmonTest\\" : "";
    $record = $prefix . "netmon_record_download";
    $load = $prefix . "netmon_load_stats";
    $update = $prefix . "netmon_json_update";
    $config = ["stats_path" => $payload["path"], "max_recent_events" => $payload["max_events"] ?? 200];
    $_GET = [];
    $_SERVER = [];
    $successes = 0;
    $failures = 0;
    $start = $payload["start"] ?? "";
    while ($start !== "" && !is_file($start)) {
        usleep(1000);
        clearstatcache(true, $start);
    }
    $begin = hrtime(true);
    if (($payload["action"] ?? "record") === "record") {
        for ($i = 0; $i < ($payload["iterations"] ?? 1); $i++) {
            $source = isset($payload["source"])
                ? base64_decode($payload["source"], true)
                : ($payload["prefix"] ?? "visitor-") . $i . str_repeat("x", $payload["source_padding"] ?? 0);
            $id = !empty($payload["rotate_files"]) ? "file-" . ($i % $payload["rotate_files"]) : ($payload["id"] ?? "artifact");
            $result = $record($config, $id, "Test artifact", "/artifact.bin", $source);
            $successes += $result ? 1 : 0;
            $failures += $result ? 0 : 1;
        }
    } elseif (($payload["action"] ?? "") === "output-budget") {
        $result = $update($payload["path"], static function (array $state) use ($payload, $prefix): array {
            if (($payload["kind"] ?? "") === "structure") {
                $state["extra"] = array_fill(0, constant($prefix . "NETMON_JSON_MAX_TOKENS"), 0);
            } elseif (($payload["kind"] ?? "") === "serialize") {
                $state["extra"] = INF;
            } else {
                $state["extra"] = str_repeat("x", constant($prefix . "NETMON_JSON_MAX_BYTES") + 1);
            }
            return $state;
        });
        $successes += $result ? 1 : 0;
        $failures += $result ? 0 : 1;
    }
    $recordSeconds = (hrtime(true) - $begin) / 1e9;
    // Capture counters before this final read, to prove pre-decode/pre-read guards.
    $decodes = $GLOBALS["limit_decodes"];
    $reads = $GLOBALS["limit_reads"];
    $stats = !empty($payload["skip_load"]) ? null : $load($config);
    echo json_encode([
        "successes" => $successes, "failures" => $failures, "stats" => $stats,
        "decodes" => $decodes, "read_lengths" => $reads,
        "final_decodes" => $GLOBALS["limit_decodes"], "final_read_lengths" => $GLOBALS["limit_reads"],
        "record_seconds" => $recordSeconds, "peak_bytes" => memory_get_peak_usage(true),
        "budgets" => array_map(static function (string $name) use ($prefix) {
            return constant($prefix . $name);
        }, ["NETMON_STATS_SOURCE_BYTES", "NETMON_STATS_GLOBAL_SOURCES", "NETMON_STATS_FILE_SOURCES",
            "NETMON_JSON_MAX_BYTES", "NETMON_JSON_MAX_TOKENS", "NETMON_JSON_MAX_DEPTH"]),
    ], JSON_THROW_ON_ERROR);
}
