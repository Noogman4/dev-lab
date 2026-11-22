"""Local, source-specific analysis instructions; no system collection or transport."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AnalysisProfile:
    key: str
    label: str
    aliases: tuple[str, ...]
    focus: frozenset[str]
    task: str
    checks: str
    answer: str


def _profile(key, label, aliases, focus, task, checks, answer):
    return AnalysisProfile(
        key,
        label,
        tuple(aliases.split("|")),
        frozenset(focus.split()),
        task,
        checks,
        answer,
    )


PROFILES = (
    _profile(
        "system",
        "Gesamter Systemcheck",
        "systemcheck|system check|gesamtanalyse|gesamtcheck|system overview",
        "security dns network process firewall performance optimization rootkit",
        "Erstelle eine zusammenhängende Gesamtbewertung der vorliegenden NetMon-Bereiche.",
        "Verbinde DNS, VPN, Routing, Firewall, Verbindungen, Prozesse und Persistenz nur bei passenden Belegen. "
        "Trenne lokale Scanergebnisse, alte Anzeigen und nicht geprüfte Bereiche. Fehlende Daten sind keine Entwarnung. "
        "Dedupliziere mehrfach sichtbare Ereignisse, benenne Widersprüche und fehlende Zeitbezüge. "
        "Leite aus einem einzelnen Scannerbefund keinen bestätigten Angriff ab.",
        "Abdeckung und Datenalter; priorisierte Gesamtbefunde mit Bereich/Beleg/Sicherheit der Aussage; "
        "bereichsübergreifende Zusammenhänge; danach ein geordneter Prüf- und Maßnahmenplan.",
    ),
    _profile(
        "roots",
        "Roots Baseline Guard",
        "roots baseline|roots guard",
        "security process rootkit",
        "Vergleiche den gemeldeten Zustand mit der ausdrücklich benannten Baseline.",
        "Unterscheide Inhalts-, Metadaten-, Paket- und Versionsänderungen. Eine Abweichung ist kein Malwarebeweis. "
        "Beachte genehmigte Updates und die Herkunft der Baseline. Keine ungeprüfte Wiederherstellung empfehlen.",
        "Konkrete Abweichung; mögliche legitime Ursache; belastbare Risikosignale; gezielter nächster Vergleich.",
    ),
    _profile(
        "startup",
        "Startup Guard",
        "startup guard|autostart",
        "security process rootkit",
        "Bewerte den konkreten Autostart- oder systemd-Eintrag und seine Änderung.",
        "Trenne Benutzer- und Systemkontext, Exec-Ziel, Aktivierungsweg und Berechtigungen. "
        "Behaupte keine Malware allein wegen eines unbekannten Namens oder temporären Pfads.",
        "Startmechanismus und Zweck; neue/geänderte Bestandteile; Risiko mit Belegen; gezielte Prüfung vor Deaktivierung.",
    ),
    _profile(
        "path",
        "PATH Guard",
        "path guard",
        "security process rootkit",
        "Prüfe PATH-Manipulationen anhand der Reihenfolge und der tatsächlichen Pfadrechte.",
        "Achte auf /tmp, /var/tmp, /dev/shm, '.', $PWD und Shell-Profiländerungen. "
        "Behaupte nicht, dass Malware sicher vorhanden ist.",
        "Wirksame Suchreihenfolge; überschattbare Programme und Schreibrechte; sichere Verifikation der einzelnen Auffälligkeit.",
    ),
    _profile(
        "repository",
        "Repository Guard",
        "repository guard|repository sources|paketquellen",
        "security",
        "Bewerte die ausgewählten Paketquellen oder Repository-Funde.",
        "Trenne Herkunft, Signaturprüfung, Schlüsselbindung, Distribution und Versionskompatibilität. "
        "Ein Fremdrepository ist nicht automatisch bösartig; keine Quelle oder Schlüsseldatei blind löschen.",
        "Quelle und Vertrauenskette; konkrete Abweichung; Upgrade-/Abhängigkeitsrisiko; nächster sicherer Abgleich.",
    ),
    _profile(
        "process",
        "Process Guard / Prozesse",
        "process guard|prozess|htop|process analysis",
        "security process performance rootkit",
        "Analysiere die gezeigten Prozesse statt allgemeine Netzwerkempfehlungen zu wiederholen.",
        "Verbinde PID, Elternprozess, Benutzer, Binärpfad, Startzeit und Ressourcenverbrauch soweit vorhanden. "
        "Hohe CPU-Last ist kein Malwarebeweis. PID-Wiederverwendung und Momentaufnahmen beachten.",
        "Prozessrolle; auffällige Beziehung oder Last; Risiko beziehungsweise Engpass; nächster gezielter Prüfschritt.",
    ),
    _profile(
        "dns",
        "DNS",
        "dns|resolver",
        "dns network security",
        "Untersuche die vorgelegte Resolverkonfiguration und Namensauflösung.",
        "Ordne Resolver den Interfaces, Such-/Routingdomains, VPN und Split-DNS zu. "
        "Trenne konfigurierte Resolver von gemessenen DNS-Anfragen. Keine Leak-Freiheit aus einer Liste ableiten. "
        "DoT und DNSSEC im konkreten VPN-/Resolverkontext beurteilen, keine pauschalen Sollwerte erfinden.",
        "Auflösungsweg; belegte Konflikte; Aussagegrenzen der Leak-Prüfung; sichere nächste Verifikation.",
    ),
    _profile(
        "vpn",
        "VPN / WireGuard",
        "wireguard|vpn",
        "dns network firewall security",
        "Bewerte Tunnelzustand, Routen und Isolation des ausgewählten VPN-Kontexts.",
        "Handshake-Alter, AllowedIPs, Routing, Resolver und Kill-Switch nur anhand vorhandener Daten verbinden. "
        "Ein aktives Interface allein beweist keinen nutzbaren Tunnel oder Leak-Schutz. Keine Schlüssel wiedergeben.",
        "Tunnel und Verkehrsweg; DNS-/Firewall-Zusammenhang; belegte Lücke; Prüfung vor einer Routen- oder Regeländerung.",
    ),
    _profile(
        "firewall",
        "Firewall",
        "firewall|ufw|nftables",
        "firewall network security",
        "Analysiere das gezeigte Regelwerk und seine konkrete Verkehrswirkung.",
        "Beachte Default-Policies, Richtung, Interface, Reihenfolge sowie IPv4/IPv6. "
        "Offene Listener und von außen erreichbare Dienste unterscheiden. Einzelne Blocks sind kein Angriffsbeweis. "
        "Keine pauschale Freigabe und kein Flush des Regelwerks empfehlen.",
        "Wirksame Regelabsicht; Lücke oder Konflikt mit Beleg; mögliche Aussperrung; kleinste überprüfbare Maßnahme.",
    ),
    _profile(
        "connections",
        "Verbindungen",
        "verbindungen|connections|connection analyse",
        "network process security",
        "Ordne die ausgewählten Verbindungen ihren lokalen Prozessen und Diensten zu.",
        "Unterscheide Listener und ausgehende Sessions, lokale und entfernte Endpunkte, Protokoll und Zustand. "
        "Ports oder IP-Adressen allein begründen keinen Malwarebefund; keine ungeprüfte Remote-Reputation behaupten.",
        "Verbindung und Prozessrolle; erwartetes Verhalten; konkrete Abweichung; gezielter Abgleich.",
    ),
    _profile(
        "capture",
        "Packet Capture",
        "packet capture|wireshark|tshark|paketmitschnitt",
        "network dns security",
        "Interpretiere die vorliegenden Paket- oder Captureinformationen.",
        "Trenne Capturefilter, Displayfilter, Zeitbezug, Paketverlust und Snaplen. "
        "Verschlüsselter Inhalt kann ohne passende Schlüssel nicht als gelesen gelten. "
        "Keine neue Liveaufzeichnung oder Payloadübertragung voraussetzen.",
        "Erfassungsgrenze; belegte Protokoll-/Kommunikationsfolge; Auffälligkeit; eng begrenzte weitere Prüfung.",
    ),
    _profile(
        "nmap",
        "Nmap",
        "nmap|portscan",
        "network security firewall",
        "Bewerte den vorliegenden Portscan mit seinem tatsächlichen Scanumfang.",
        "Offen, geschlossen und gefiltert unterscheiden. Dienste-/Versionsangaben sind Erkennungsergebnisse. "
        "Ein offener Port ist keine nachgewiesene Schwachstelle. Fehlende Hosts oder UDP-Daten nicht erfinden.",
        "Scanabdeckung; erreichbare Dienste; konkrete Exposition; gezielte Verifikation ohne ungefragten Folgescan.",
    ),
    _profile(
        "route",
        "MTR / Traceroute",
        "mtr|traceroute|trace analyse|trace analysis",
        "network performance",
        "Erkläre den gezeigten Pfad und die Messung von Erreichbarkeit und Laufzeit.",
        "ICMP-Drosselung einzelner Zwischenhops von Verlust bis zum Ziel unterscheiden. "
        "Asymmetrische Wege und begrenzte Messzeiträume berücksichtigen; kein Angriffsverdacht allein wegen eines Hops.",
        "Zielerreichbarkeit; belastbare Verlust-/Latenzstelle; Messgrenzen; gezielter Vergleich.",
    ),
    _profile(
        "traffic",
        "iftop / Datenverkehr",
        "iftop|bandbreite|traffic",
        "network performance process",
        "Untersuche die gezeigte Bandbreitennutzung auf dem ausgewählten Interface.",
        "Einheiten, Sende-/Empfangsrichtung, Messintervall und Summen unterscheiden. "
        "Kurzzeitspitzen und anhaltende Last trennen. Ohne Prozessdaten keinen Verursacher behaupten.",
        "Dominante Flüsse; Last und Zeitraum; plausible Erklärung; nächste begrenzte Zuordnung.",
    ),
    _profile(
        "lynis",
        "Lynis",
        "lynis",
        "security optimization",
        "Bewerte die konkreten Lynis-Tests im Kontext des eingesetzten Systems.",
        "Test-IDs, Warnungen und Vorschläge unterscheiden. Ein Hardening-Index ist kein Kompromittierungsnachweis. "
        "Abhängigkeiten und Nebenwirkungen von Härtungsmaßnahmen vor ihrer Empfehlung benennen.",
        "Test-ID und Befund; tatsächliche Relevanz; priorisierte Maßnahme mit Nebenwirkung und Kontrolle.",
    ),
    _profile(
        "rkhunter",
        "rkhunter",
        "rkhunter|rootkit hunter",
        "security rootkit process",
        "Ordne rkhunter-Warnungen vorsichtig anhand konkreter Belege ein.",
        "Legitime Paketupdates und veraltete Referenzen als mögliche Ursache prüfen. "
        "Warnungen sind keine bestätigten Rootkits. Referenzdaten nicht blind aktualisieren, um Warnungen zu beseitigen.",
        "Warnung und geprüfte Referenz; mögliche legitime Ursache; unabhängiger Nachweis; nächster Prüfschritt.",
    ),
    _profile(
        "clamav",
        "ClamAV",
        "clamav|clamscan|clamd",
        "security",
        "Bewerte den konkreten Scannerlauf und seine Funde.",
        "Signaturstand, Scanumfang, übersprungene Dateien, Fehler und PUA von Malwaretreffern unterscheiden. "
        "Quarantäne oder Löschung sind gesonderte Entscheidungen; keine Entwarnung für ungeprüfte Bereiche.",
        "Abdeckung; Fundtyp und Dateibeleg; Validierung vor Quarantäne; priorisierte weitere Prüfung.",
    ),
    _profile(
        "storage",
        "HDD / Datenträger",
        "hdd|datenträger|laufwerk|luks|smart analyse",
        "security performance",
        "Erkläre Zustand und Zuordnung der gezeigten Laufwerks-/Dateisystemdaten.",
        "Gerät, Partition, Dateisystem, Verschlüsselung und Mountpunkt auseinanderhalten. "
        "SMART-Indikatoren sind keine Ausfallgarantie. Keine Schreibtests, Reparaturen oder Formatierung ohne gesonderte Freigabe.",
        "Gerätezuordnung und Messgrenze; konkrete Warnindikatoren; Datensicherungsbedarf; zunächst lesende Verifikation.",
    ),
    _profile(
        "devices",
        "Geräte / Eingabezugriffe",
        "connected devices|geräte|devices|input access",
        "security process network",
        "Bewerte die vorhandenen Geräte- und Zugriffsangaben.",
        "Geräteidentität, Klasse, Treiber und beobachteten Zugriff trennen. Ein unbekannter Herstellername reicht nicht "
        "für einen Angriffsverdacht. Berechtigte Desktop-/Eingabedienste berücksichtigen.",
        "Gerät und Zugriffsrolle; konkrete Abweichung; überprüfbare Zuordnung; Maßnahme erst nach Verifikation.",
    ),
    _profile(
        "logs",
        "System- und NetMon-Logs",
        "system log|system-log|netmon log|journal",
        "security process network",
        "Rekonstruiere aus den ausgewählten Logzeilen einen nachvollziehbaren Ereignisverlauf.",
        "Zeitstempel, Dienst, Wiederholungen, Neustarts und Folgefehler trennen. "
        "Zitierte Fehlermeldungen und echte Ursachen auseinanderhalten. Eine Textauswahl ist kein vollständiges Journal.",
        "Zeitleiste; erster belastbarer Fehler; Folgeereignisse; nächste gezielte Datenlücke.",
    ),
    _profile(
        "linux",
        "Linux-Hilfe",
        "linux hilfe|linux help|linux command",
        "security",
        "Erkläre den ausgewählten Linux-Befehl beziehungsweise Dokumentationsausschnitt.",
        "Implementierung und Version, Rechte, Argumente, Schreibwirkungen und Beispielvoraussetzungen konkret nennen. "
        "Nicht geprüfte Beispiele und tatsächliche Ergebnisse unterscheiden. Keine Befehle automatisch ausführen.",
        "Zweck; Argumente und Wirkung; Risiko; ein passender begrenzter Übungs- oder Prüfschritt.",
    ),
    _profile(
        "security",
        "Security",
        "security|sicherheit",
        "security process firewall rootkit",
        "Bewerte die vorliegenden Sicherheitsereignisse nach Belegen statt nach Alarmworten.",
        "Erkennung, Verdacht und bestätigten Befund trennen. Normale Hintergrundereignisse, "
        "Wiederholungen und wirkliche Auswirkungen auseinanderhalten.",
        "Befund mit Beleg und Aussagegrenze; Priorität; unabhängige Prüfung vor einer Änderung.",
    ),
)
GENERAL = _profile(
    "general",
    "Ausgewählter Bereich",
    "",
    "security dns network process firewall performance optimization rootkit",
    "Bewerte ausschließlich den ausgewählten Inhalt und benenne fehlenden Kontext.",
    "Keine Systemzustände oder angrenzenden Bereiche ohne Beleg hinzuerfinden.",
    "Beobachtung; Bedeutung; begründete Priorität; gezielte nächste Prüfung.",
)


def profile_for_title(title):
    normalized = re.sub(r"[^\w]+", " ", str(title or "").casefold()).strip()
    for profile in PROFILES:
        if any(
            re.sub(r"[^\w]+", " ", alias).strip() in normalized
            for alias in profile.aliases
        ):
            return profile
    return GENERAL
