<?php

declare(strict_types=1);

// Der Statistik-Token darf nicht im Repo oder Build-Artefakten stehen.
// Produktive Deployments muessen NETMON_STATS_TOKEN serverseitig setzen.
$statsToken = trim((string) getenv("NETMON_STATS_TOKEN"));

return [
    "stats_token" => $statsToken,
    "stats_path" => __DIR__ . "/data/download-stats.json",
    "max_recent_events" => 200,
    "downloads" => [
        "netmon-deb" => [
            "label" => "NetMon 1.1.19 package (.deb)",
            "target" => "/dist/netmon_1.1.19_all.deb",
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
            "label" => "NetMon documentation HTML 1.1.19",
            "target" => "/dist/docs/netmon_dokumentation_1.1.19.html",
        ],
        "docs-pdf" => [
            "label" => "NetMon documentation PDF 1.1.19",
            "target" => "/dist/docs/netmon_dokumentation_1.1.19.pdf",
        ],
        "audit-pdf" => [
            "label" => "NetMon security audit PDF 2026",
            "target" => "/netmon_security_audit_2026_r9.pdf",
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
