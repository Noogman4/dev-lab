<?php

declare(strict_types=1);

// Der Statistik-Token darf nicht im Repo oder Build-Artefakten stehen.
// Pflicht: serverseitig an PHP uebergeben, 1..512 RFC-6750-Tokenzeichen.
// Fehlende/ungueltige Konfiguration sperrt die Statistik mit HTTP 503.
// Client-Zugriff ausschliesslich per Authorization: Bearer (nie per URL).
$statsToken = getenv("NETMON_STATS_TOKEN");

return [
    "stats_token" => $statsToken,
    "stats_path" => __DIR__ . "/data/download-stats.json",
    "max_recent_events" => 200,
    "downloads" => [
        "netmon-deb" => [
            "label" => "NetMon 1.1.21 package (.deb)",
            "target" => "/dist/netmon_1.1.21_all.deb",
        ],
        "sha256sums" => [
            "label" => "SHA256SUMS",
            "target" => "/dist/SHA256SUMS",
        ],
        "sha256sums-minisig" => [
            "label" => "SHA256SUMS Minisign signature",
            "target" => "/dist/SHA256SUMS.minisig",
        ],
        "docs-html" => [
            "label" => "NetMon documentation HTML 1.1.21",
            "target" => "/dist/docs/netmon_dokumentation_1.1.21.html",
        ],
        "docs-pdf" => [
            "label" => "NetMon documentation PDF 1.1.21",
            "target" => "/dist/docs/netmon_dokumentation_1.1.21.pdf",
        ],
        "audit-pdf" => [
            "label" => "NetMon security audit PDF 2026, round 12",
            "target" => "/netmon_security_audit_2026_r12.pdf",
        ],
        "verify-download-script" => [
            "label" => "Download verification script",
            "target" => "/verify/verify_netmon_download.sh",
        ],
        "verify-signature-script" => [
            "label" => "Signature verification script",
            "target" => "/verify/verify_netmon_signature.sh",
        ],
        "minisign-pubkey" => [
            "label" => "NetMon Minisign public key",
            "target" => "/verify/netmonroots.minisign.pub",
        ],
    ],
];
