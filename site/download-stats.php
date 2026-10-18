<?php

declare(strict_types=1);

require __DIR__ . "/download-lib.php";

$config = netmon_download_config();
netmon_require_stats_token($config);
$statsAvailable = false;
$stats = netmon_load_stats($config, $statsAvailable);
$files = (array) ($stats["files"] ?? []);
$sources = (array) ($stats["sources"] ?? []);
$days = (array) ($stats["days"] ?? []);
$recentEvents = (array) ($stats["recent_events"] ?? []);

uasort($files, static function (array $left, array $right): int {
    return (int) ($right["count"] ?? 0) <=> (int) ($left["count"] ?? 0);
});
arsort($sources);
krsort($days);

$statsPath = (string) ($config["stats_path"] ?? "");
$storageState = "OK";
if ($statsPath === "" || !file_exists($statsPath)) {
    $storageState = "Noch keine Datei angelegt";
} elseif (!is_writable(dirname($statsPath)) || !is_readable($statsPath)
    || is_link($statsPath) || is_link($statsPath . ".lock")) {
    $storageState = "Nicht schreibbar";
} elseif (!$statsAvailable) {
    $storageState = "Nicht lesbar oder Statistiklimit ueberschritten";
}

header("Content-Type: text/html; charset=utf-8");
?>
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NetMon Download Statistik</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #09111a;
      --panel: #0f1c29;
      --line: #244055;
      --text: #ecf4fb;
      --muted: #9fb5c7;
      --accent: #8bd3ff;
      --good: #7fe3a1;
      --warn: #ffd27a;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI", Tahoma, sans-serif; background: linear-gradient(180deg, #06101a 0%, #0b1622 100%); color: var(--text); }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }
    h1, h2 { margin: 0 0 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 20px 0 28px; }
    .card { background: rgba(15, 28, 41, 0.92); border: 1px solid var(--line); border-radius: 16px; padding: 18px; }
    .value { display: block; margin-top: 6px; font-size: 1.8rem; font-weight: 700; color: var(--accent); }
    .muted { color: var(--muted); }
    .warn { color: var(--warn); }
    .good { color: var(--good); }
    .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin: 16px 0 4px; }
    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid rgba(139, 211, 255, 0.35);
      background: rgba(139, 211, 255, 0.12);
      color: var(--text);
      text-decoration: none;
      cursor: pointer;
      font: inherit;
    }
    .button:hover { background: rgba(139, 211, 255, 0.18); }
    .toolbar label { display: inline-flex; gap: 8px; align-items: center; color: var(--muted); }
    .toolbar input { accent-color: var(--accent); }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; background: rgba(15, 28, 41, 0.82); }
    th, td { padding: 12px 14px; border-bottom: 1px solid rgba(36, 64, 85, 0.75); text-align: left; vertical-align: top; font-size: 0.96rem; }
    th { color: var(--muted); font-weight: 600; background: rgba(21, 38, 56, 0.95); }
    tr:last-child td { border-bottom: 0; }
    code { color: var(--accent); font-family: "Consolas", "Menlo", monospace; font-size: 0.92rem; }
    .section { margin-top: 30px; }
    .pill { display: inline-block; padding: 4px 10px; border-radius: 999px; background: rgba(139, 211, 255, 0.12); border: 1px solid rgba(139, 211, 255, 0.25); color: var(--accent); font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>NetMon Download Statistik</h1>
    <p class="muted">Serverseitig gezaehlte Downloads ueber <code>download.php</code>. Stand: <strong><?php echo netmon_html((string) ($stats["updated_at"] ?: "noch kein Eintrag")); ?></strong></p>
    <div class="toolbar">
      <button class="button" type="button" id="reload-stats">Neu laden</button>
      <label>
        <input type="checkbox" id="auto-refresh" checked>
        Auto-Refresh alle 15 Sekunden
      </label>
    </div>

    <div class="grid">
      <div class="card"><div>Gesamt-Downloads</div><span class="value"><?php echo (int) ($stats["total_downloads"] ?? 0); ?></span></div>
      <div class="card"><div>Dateien mit Downloads</div><span class="value"><?php echo count($files); ?></span></div>
      <div class="card"><div>Quellen</div><span class="value"><?php echo count($sources); ?></span></div>
      <div class="card"><div>Speicherstatus</div><span class="value <?php echo $storageState === "OK" ? "good" : "warn"; ?>"><?php echo netmon_html($storageState); ?></span></div>
    </div>

    <div class="section">
      <h2>Downloads pro Datei</h2>
      <table>
        <thead>
          <tr><th>Datei</th><th>Ziel</th><th>Anzahl</th><th>Letzter Download</th><th>Quellen</th></tr>
        </thead>
        <tbody>
        <?php if (!$files): ?>
          <tr><td colspan="5">Noch keine Downloads gezaehlt.</td></tr>
        <?php else: ?>
          <?php foreach ($files as $fileId => $entry): ?>
            <?php
              $entrySources = (array) ($entry["sources"] ?? []);
              arsort($entrySources);
              $sourceParts = [];
              foreach ($entrySources as $sourceName => $count) {
                  $sourceParts[] = $sourceName . ": " . (int) $count;
              }
            ?>
            <tr>
              <td><strong><?php echo netmon_html((string) ($entry["label"] ?? $fileId)); ?></strong><br><span class="muted"><code><?php echo netmon_html((string) $fileId); ?></code></span></td>
              <td><code><?php echo netmon_html((string) ($entry["target"] ?? "")); ?></code></td>
              <td><?php echo (int) ($entry["count"] ?? 0); ?></td>
              <td><?php echo netmon_html((string) ($entry["last_download_at"] ?? "-")); ?></td>
              <td><?php echo netmon_html($sourceParts ? implode(" | ", $sourceParts) : "-"); ?></td>
            </tr>
          <?php endforeach; ?>
        <?php endif; ?>
        </tbody>
      </table>
    </div>

    <div class="section">
      <h2>Quellen</h2>
      <table>
        <thead>
          <tr><th>Quelle</th><th>Downloads</th></tr>
        </thead>
        <tbody>
        <?php if (!$sources): ?>
          <tr><td colspan="2">Noch keine Quellzuordnung vorhanden.</td></tr>
        <?php else: ?>
          <?php foreach ($sources as $sourceName => $count): ?>
            <tr><td><code><?php echo netmon_html((string) $sourceName); ?></code></td><td><?php echo (int) $count; ?></td></tr>
          <?php endforeach; ?>
        <?php endif; ?>
        </tbody>
      </table>
    </div>

    <div class="section">
      <h2>Tage</h2>
      <table>
        <thead>
          <tr><th>Tag</th><th>Downloads</th></tr>
        </thead>
        <tbody>
        <?php if (!$days): ?>
          <tr><td colspan="2">Noch keine Tageswerte vorhanden.</td></tr>
        <?php else: ?>
          <?php foreach ($days as $day => $count): ?>
            <tr><td><code><?php echo netmon_html((string) $day); ?></code></td><td><?php echo (int) $count; ?></td></tr>
          <?php endforeach; ?>
        <?php endif; ?>
        </tbody>
      </table>
    </div>

    <div class="section">
      <h2>Letzte Ereignisse</h2>
      <table>
        <thead>
          <tr><th>Zeit</th><th>Datei</th><th>Quelle</th><th>Sprache</th><th>Referrer</th><th>IP-Hash</th></tr>
        </thead>
        <tbody>
        <?php if (!$recentEvents): ?>
          <tr><td colspan="6">Noch keine Ereignisse vorhanden.</td></tr>
        <?php else: ?>
          <?php foreach ($recentEvents as $event): ?>
            <tr>
              <td><?php echo netmon_html((string) ($event["timestamp"] ?? "-")); ?></td>
              <td><strong><?php echo netmon_html((string) ($event["label"] ?? "-")); ?></strong><br><span class="muted"><code><?php echo netmon_html((string) ($event["id"] ?? "-")); ?></code></span></td>
              <td><?php echo netmon_html((string) ($event["source"] ?? "-")); ?></td>
              <td><?php echo netmon_html((string) ($event["lang"] ?? "-")); ?></td>
              <td><?php echo netmon_html((string) ($event["referrer"] ?? "-")); ?></td>
              <td><span class="pill"><?php echo netmon_html((string) ($event["ip_hash"] ?? "")); ?></span></td>
            </tr>
          <?php endforeach; ?>
        <?php endif; ?>
        </tbody>
      </table>
    </div>

    <div class="section">
      <p class="muted"><code>__other__</code> fasst weitere Herkunftsbezeichnungen zusammen, wenn das Quellenlimit erreicht ist.</p>
      <p class="muted">Hinweis: Die Seite zaehlt nur Downloads, die ueber <code>download.php</code> laufen. Direkte Aufrufe auf <code>/dist/...</code> erscheinen hier nicht.</p>
    </div>
  </div>
  <script>
    (function () {
      const reloadButton = document.getElementById("reload-stats");
      const autoRefresh = document.getElementById("auto-refresh");
      let timerId = null;

      function reloadWithCacheBuster() {
        const url = new URL(window.location.href);
        url.searchParams.set("t", String(Date.now()));
        window.location.replace(url.toString());
      }

      function scheduleRefresh() {
        if (timerId) {
          window.clearInterval(timerId);
          timerId = null;
        }
        if (!autoRefresh || !autoRefresh.checked) {
          return;
        }
        timerId = window.setInterval(reloadWithCacheBuster, 15000);
      }

      if (reloadButton) {
        reloadButton.addEventListener("click", reloadWithCacheBuster);
      }
      if (autoRefresh) {
        autoRefresh.addEventListener("change", scheduleRefresh);
      }
      scheduleRefresh();
    })();
  </script>
</body>
</html>
