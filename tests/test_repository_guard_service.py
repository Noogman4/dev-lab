from netmon.services.repository_guard_service import RepositoryGuardService


def test_collect_sources_parses_valid_and_disabled_entries(tmp_path):
    sources_file = tmp_path / "sources.list"
    sources_file.write_text(
        "\n".join(
            [
                "deb https://deb.debian.org/debian bookworm main",
                "# deb https://ppa.launchpadcontent.net/demo/stable ubuntu main",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert errors == []
    assert len(sources) == 2
    assert sources[0]["enabled"] is True
    assert sources[0]["host"] == "deb.debian.org"
    assert sources[0]["origin_class"] == "known"
    assert sources[1]["enabled"] is False
    assert sources[1]["repo_type"] == "deb"


def test_scan_keeps_disabled_entries_as_notice_only(tmp_path):
    sources_file = tmp_path / "sources.list"
    sources_file.write_text(
        "# deb https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    result = service.scan()
    codes = [item["code"] for item in result["findings"]]

    assert codes == ["repo_disabled_entry"]
    assert result["status"] == "notice"


def test_collect_sources_parses_signed_by_option(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "deb [arch=amd64 signed-by=/usr/share/keyrings/demo.gpg] "
        "https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert errors == []
    assert len(sources) == 1
    assert sources[0]["options"]["arch"] == "amd64"
    assert sources[0]["signed_by"] == "/usr/share/keyrings/demo.gpg"
    assert sources[0]["signed_by_paths"] == ["/usr/share/keyrings/demo.gpg"]
    assert sources[0]["origin_class"] == "unknown"


def test_scan_reports_missing_signed_by_keyring_file(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "deb [signed-by=/usr/share/keyrings/missing-demo.gpg] "
        "https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(sources_file)],
        file_exists_fn=lambda path: False,
    )
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_signed_by_missing_file" in codes
    assert "repo_no_signed_by" not in codes


def test_scan_reports_unexpected_signed_by_path(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "deb [signed-by=demo.gpg] https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_signed_by_unexpected_path" in codes


def test_scan_reports_unexpected_but_existing_keyring_location(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "deb [signed-by=/opt/custom/demo.gpg] https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(sources_file)],
        file_exists_fn=lambda path: path == "/opt/custom/demo.gpg",
    )
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_signed_by_unexpected_location" in codes


def test_repository_guard_trustlist_roundtrip(tmp_path):
    trustlist_path = tmp_path / "repository_guard_trustlist.json"
    source = {
        "host": "example.invalid",
        "uri": "https://example.invalid/repo",
        "repo_type": "deb",
    }
    service = RepositoryGuardService()

    ok, err = service.mark_host_trusted(source, str(trustlist_path))
    assert ok is True
    assert err == ""

    trustlist = service.load_trustlist(str(trustlist_path))
    trusted_hosts = dict(trustlist.get("trusted_hosts") or {})
    assert "example.invalid" in trusted_hosts
    assert trusted_hosts["example.invalid"]["uri"] == "https://example.invalid/repo"


def test_scan_suppresses_unknown_origin_for_trusted_host(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "deb https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    trustlist = {
        "trusted_hosts": {
            "example.invalid": {
                "host": "example.invalid",
            }
        }
    }
    result = service.scan(trustlist=trustlist)
    codes = {item["code"] for item in result["findings"]}

    assert "repo_unknown_origin" not in codes
    assert "repo_no_signed_by" in codes
    assert result["sources"][0]["trusted_host"] is True
    assert result["sources"][0]["trust_state"] == "trusted"


def test_known_third_party_hosts_do_not_raise_unknown_origin(tmp_path):
    sources_file = tmp_path / "thirdparty.list"
    sources_file.write_text(
        "\n".join(
            [
                "deb https://brave-browser-apt-release.s3.brave.com/ stable main",
                "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable",
                "deb https://packages.zorinos.com/stable noble main",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_unknown_origin" not in codes


def test_scan_creates_http_unknown_and_missing_signed_by_findings(tmp_path):
    sources_file = tmp_path / "custom.list"
    sources_file.write_text(
        "deb http://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert result["status"] == "warning"
    assert result["summary"]["repositories_total"] == 1
    assert "repo_http_used" in codes
    assert "repo_unknown_origin" in codes
    assert "repo_no_signed_by" in codes


def test_scan_marks_duplicate_sources(tmp_path):
    first = tmp_path / "first.list"
    second = tmp_path / "second.list"
    line = "deb https://deb.debian.org/debian bookworm main\n"
    first.write_text(line, encoding="utf-8")
    second.write_text(line, encoding="utf-8")

    service = RepositoryGuardService(
        source_patterns=[str(first), str(second)]
    )
    result = service.scan()
    duplicate_findings = [
        item for item in result["findings"] if item["code"] == "repo_duplicate_source"
    ]

    assert len(duplicate_findings) == 2
    assert result["status"] == "warning"


def test_scan_marks_duplicate_source_variants(tmp_path):
    first = tmp_path / "first.list"
    second = tmp_path / "second.list"
    first.write_text(
        "deb [signed-by=/usr/share/keyrings/demo-one.gpg] "
        "https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )
    second.write_text(
        "deb [signed-by=/usr/share/keyrings/demo-two.gpg] "
        "https://example.invalid/repo stable main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(first), str(second)],
        file_exists_fn=lambda path: True,
    )
    result = service.scan()
    duplicate_findings = [
        item
        for item in result["findings"]
        if item["code"] == "repo_duplicate_source_variant"
    ]

    assert len(duplicate_findings) == 2


def test_collect_sources_reports_parse_errors(tmp_path):
    broken = tmp_path / "broken.list"
    broken.write_text("deb https://deb.debian.org/debian\n", encoding="utf-8")

    service = RepositoryGuardService(source_patterns=[str(broken)])
    sources, errors = service.collect_sources()

    assert sources == []
    assert len(errors) == 1
    assert errors[0]["code"] == "repo_parse_error"


def test_collect_sources_reports_missing_explicit_file(tmp_path):
    missing = tmp_path / "missing.list"

    service = RepositoryGuardService(source_patterns=[str(missing)])
    sources, errors = service.collect_sources()

    assert sources == []
    assert len(errors) == 1
    assert errors[0]["code"] == "repo_file_missing"


def test_collect_sources_parses_deb822_sources_blocks(tmp_path):
    sources_file = tmp_path / "debian.sources"
    sources_file.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: https://deb.debian.org/debian",
                "Suites: bookworm bookworm-updates",
                "Components: main contrib",
                "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert errors == []
    assert len(sources) == 2
    assert all(source["format"] == "deb822" for source in sources)
    assert all(source["enabled"] is True for source in sources)
    assert sources[0]["signed_by"] == "/usr/share/keyrings/debian-archive-keyring.gpg"
    assert sources[0]["signed_by_paths"] == ["/usr/share/keyrings/debian-archive-keyring.gpg"]
    assert sources[0]["host"] == "deb.debian.org"
    assert sources[0]["origin_class"] == "known"
    assert sources[0]["components"] == ["main", "contrib"]


def test_collect_sources_parses_disabled_deb822_block(tmp_path):
    sources_file = tmp_path / "thirdparty.sources"
    sources_file.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: https://example.invalid/repo",
                "Suites: stable",
                "Components: main",
                "Enabled: no",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert errors == []
    assert len(sources) == 1
    assert sources[0]["enabled"] is False
    assert sources[0]["origin_class"] == "unknown"


def test_collect_sources_detects_embedded_deb822_signed_by_key(tmp_path):
    sources_file = tmp_path / "embedded.sources"
    sources_file.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: https://ppa.launchpadcontent.net/demo/stable/ubuntu/",
                "Suites: noble",
                "Components: main",
                "Signed-By: -----BEGIN PGP PUBLIC KEY BLOCK-----",
                " .",
                " abcdef",
                " -----END PGP PUBLIC KEY BLOCK-----",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert errors == []
    assert len(sources) == 1
    assert sources[0]["signed_by_embedded"] is True
    assert sources[0]["signed_by_paths"] == []


def test_scan_does_not_flag_embedded_deb822_signed_by_as_bad_path(tmp_path):
    sources_file = tmp_path / "embedded.sources"
    sources_file.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: https://ppa.launchpadcontent.net/demo/stable/ubuntu/",
                "Suites: noble",
                "Components: main",
                "Signed-By: -----BEGIN PGP PUBLIC KEY BLOCK-----",
                " .",
                " abcdef",
                " -----END PGP PUBLIC KEY BLOCK-----",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_signed_by_unexpected_path" not in codes
    assert "repo_signed_by_missing_file" not in codes
    assert "repo_no_signed_by" not in codes


def test_collect_sources_reports_deb822_parse_errors(tmp_path):
    sources_file = tmp_path / "broken.sources"
    sources_file.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: https://deb.debian.org/debian",
                "",
            ]
        ),
        encoding="utf-8",
    )

    service = RepositoryGuardService(source_patterns=[str(sources_file)])
    sources, errors = service.collect_sources()

    assert sources == []
    assert len(errors) == 1
    assert errors[0]["code"] == "repo_parse_error"


def test_scan_collects_flatpak_remotes_when_available(tmp_path):
    sources_file = tmp_path / "sources.list"
    sources_file.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )

    outputs = {
        "system": "flathub\thttps://dl.flathub.org/repo/\t\n",
        "user": "demo\thttps://example.invalid/flatpak/\t\n",
    }

    service = RepositoryGuardService(
        source_patterns=[str(sources_file)],
        flatpak_available_fn=lambda: True,
        flatpak_runner=lambda scope: outputs[scope],
    )
    result = service.scan()
    flatpak_sources = [item for item in result["sources"] if item["kind"] == "flatpak"]
    codes = {item["code"] for item in result["findings"]}

    assert len(flatpak_sources) == 2
    assert flatpak_sources[0]["repo_type"] == "flatpak"
    assert any(item["scope"] == "system" for item in flatpak_sources)
    assert all(item["enabled"] is True for item in flatpak_sources)
    assert "repo_flatpak_remote_present" in codes
    assert "repo_flatpak_remote_untrusted_candidate" in codes


def test_scan_adds_info_when_flatpak_is_missing(tmp_path):
    sources_file = tmp_path / "sources.list"
    sources_file.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(sources_file)],
        flatpak_available_fn=lambda: False,
    )
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert "repo_flatpak_not_installed" in codes


def test_scan_reports_flatpak_query_error(tmp_path):
    sources_file = tmp_path / "sources.list"
    sources_file.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )

    def _runner(_scope):
        raise RuntimeError("flatpak failed")

    service = RepositoryGuardService(
        source_patterns=[str(sources_file)],
        flatpak_available_fn=lambda: True,
        flatpak_runner=_runner,
    )
    result = service.scan()
    codes = {item["code"] for item in result["findings"]}

    assert result["status"] == "error"
    assert "repo_flatpak_query_failed" in codes


def test_repository_guard_baseline_roundtrip_and_compare(tmp_path):
    first = tmp_path / "sources.list"
    first.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(first)],
        flatpak_available_fn=lambda: False,
    )
    initial_result = service.scan()
    baseline_path = tmp_path / "repository_guard_baseline.json"

    ok, err = service.save_baseline(str(baseline_path), initial_result["sources"])
    assert ok is True
    assert err == ""

    baseline = service.load_baseline(str(baseline_path))
    assert len(baseline["sources"]) == 1
    assert baseline["generated_at"]

    first.write_text(
        "deb https://deb.debian.org/debian bookworm-updates main\n",
        encoding="utf-8",
    )
    changed_result = service.scan()
    comparison = service.compare_to_baseline(baseline, changed_result["sources"])

    assert comparison["new"] == []
    assert comparison["removed"] == []
    assert len(comparison["changed"]) == 1
    assert comparison["changed"][0]["before"]["suite"] == "bookworm"
    assert comparison["changed"][0]["after"]["suite"] == "bookworm-updates"


def test_repository_guard_baseline_detects_moved_source_without_false_new_removed(tmp_path):
    first = tmp_path / "sources.list"
    first.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )

    service = RepositoryGuardService(
        source_patterns=[str(first)],
        flatpak_available_fn=lambda: False,
    )
    initial_result = service.scan()
    baseline = {"sources": initial_result["sources"]}

    second = tmp_path / "moved.list"
    second.write_text(
        "deb https://deb.debian.org/debian bookworm main\n",
        encoding="utf-8",
    )
    service.source_patterns = [str(second)]
    moved_result = service.scan()
    comparison = service.compare_to_baseline(baseline, moved_result["sources"])

    assert comparison["new"] == []
    assert comparison["removed"] == []
    assert comparison["changed"] == []
    assert len(comparison["moved"]) == 1
    assert comparison["moved"][0]["before"]["file_path"].endswith("sources.list")
    assert comparison["moved"][0]["after"]["file_path"].endswith("moved.list")
