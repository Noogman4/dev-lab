from pathlib import Path

import browser_container_builder as builder


def make_firefox_source_tree(base_dir: Path) -> Path:
    source_dir = base_dir / "firefox-source"
    icon_dir = source_dir / "browser" / "chrome" / "icons" / "default"
    icon_dir.mkdir(parents=True)
    (source_dir / "firefox").write_text("#!/bin/sh\n", encoding="utf-8")
    (icon_dir / "default128.png").write_text("png", encoding="utf-8")
    return source_dir


def test_validate_config_payload_uses_base_dir_default() -> None:
    base_dir = Path("/tmp/example")
    payload = {
        "containers": [
            {
                "name": "firefox-GitHub",
                "allowed_domains": ["github.com"],
            }
        ]
    }

    specs = builder.validate_config_payload(payload, base_dir)

    assert specs[0].path == base_dir / "firefox-GitHub"
    assert specs[0].source_firefox_dir is None
    assert specs[0].homepage_url is None
    assert specs[0].new_tab_url is None
    assert specs[0].menu_name is None


def test_validate_config_payload_reads_homepage_and_new_tab() -> None:
    base_dir = Path("/tmp/example")
    payload = {
        "containers": [
            {
                "name": "firefox-GitHub",
                "allowed_domains": ["github.com"],
                "homepage_url": "https://github.com",
                "new_tab_url": "about:blank",
                "menu_name": "NetMon Secure Browser – GitHub",
            }
        ]
    }

    specs = builder.validate_config_payload(payload, base_dir)

    assert specs[0].homepage_url == "https://github.com"
    assert specs[0].new_tab_url == "about:blank"
    assert specs[0].menu_name == "NetMon Secure Browser – GitHub"


def test_build_policies_payload_blocks_all_and_allows_domains() -> None:
    spec = builder.ContainerSpec(
        name="firefox-OpenAI",
        path=Path("/tmp/firefox-OpenAI"),
        allowed_domains=["openai.com", "platform.openai.com", "netmonroots.com:2083"],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://chatgpt.com",
        new_tab_url="about:blank",
    )

    payload = builder.build_policies_payload(spec)
    homepage = payload["policies"]["Homepage"]
    website_filter = payload["policies"]["WebsiteFilter"]

    assert homepage["URL"] == "https://chatgpt.com"
    assert homepage["StartPage"] == "homepage"
    assert website_filter["Block"] == ["<all_urls>"]
    assert "*://openai.com/*" in website_filter["Exceptions"]
    assert "*://*.openai.com/*" in website_filter["Exceptions"]
    assert "*://platform.openai.com/*" in website_filter["Exceptions"]
    assert "https://netmonroots.com/*" in website_filter["Exceptions"]


def test_build_user_js_content_sets_homepage_and_blank_new_tab() -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        allowed_domains=["github.com"],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://github.com",
        new_tab_url="about:blank",
    )

    content = builder.build_user_js_content(spec)

    assert 'user_pref("browser.startup.homepage", "https://github.com");' in content
    assert 'user_pref("browser.newtabpage.enabled", false);' in content
    assert 'user_pref("browser.newtab.url", "about:blank");' in content


def test_build_container_readme_mentions_homepage() -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        allowed_domains=["github.com"],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://github.com",
        new_tab_url="about:blank",
    )

    readme = builder.build_container_readme(spec)

    assert "Startseite" in readme
    assert "https://github.com" in readme
    assert "about:blank" in readme
    assert "netmon-secure-browser-firefox-github.desktop" in readme


def test_build_menu_launcher_content_uses_menu_fields() -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        allowed_domains=["github.com"],
        source_firefox_dir=Path("/tmp/source"),
        menu_name="NetMon Secure Browser – GitHub",
    )

    content = builder.build_menu_launcher_content(spec)

    assert "Type=Application" in content
    assert "Terminal=false" in content
    assert "Categories=Network;Security;" in content
    assert "Name=NetMon Secure Browser – GitHub" in content
    assert "Exec=/tmp/firefox-GitHub/start.sh" in content


def test_score_profile_match_counts_expected_domain_hits() -> None:
    profile = builder.FirefoxProfile(
        path=Path("/tmp/profile"),
        domains=["chatgpt.com", "cdn.openai.com", "auth.openai.com"],
        sources=["places.sqlite"],
    )

    score, matched_domains = builder.score_profile_match(
        profile, ["chatgpt.com", "openai.com", "auth.openai.com"]
    )

    assert score == 3
    assert matched_domains == ["chatgpt.com", "openai.com", "auth.openai.com"]


def test_correlate_profiles_sets_likely_profile_and_suggestion() -> None:
    container = builder.DiscoveredContainer(
        name="firefox-chatgpt",
        root_dir=Path("/tmp/firefox-chatgpt"),
        binary_path=Path("/tmp/firefox-chatgpt/firefox/firefox"),
        version="148.0",
        profile_path=None,
        start_command=None,
        domains=["chatgpt.com"],
        purpose="OpenAI",
        risk_hints=[],
    )
    profile = builder.FirefoxProfile(
        path=Path("/home/happy/.mozilla/firefox/example.default-release"),
        domains=["chatgpt.com", "auth.openai.com", "openai.com"],
        sources=["places.sqlite", "prefs.js"],
    )

    builder.correlate_profiles([container], [profile])

    assert container.correlated_profile_path == profile.path
    assert "chatgpt.com" in (container.correlation_reason or "")
    assert "keine automatische Aenderung bestehender Container" not in (
        container.correlation_reason or ""
    )
    assert container.start_script_suggestion is not None
    assert '--profile "/home/happy/.mozilla/firefox/example.default-release"' in (
        container.start_script_suggestion
    )


def test_parse_args_accepts_only_option() -> None:
    args = builder.parse_args(["--only", "firefox-GitHub"])

    assert args.only == "firefox-GitHub"
    assert args.apply is False


def test_filter_by_only_limits_processed_items() -> None:
    containers = [
        builder.DiscoveredContainer(
            name="firefox-chatgpt",
            root_dir=Path("/tmp/firefox-chatgpt"),
            binary_path=Path("/tmp/firefox-chatgpt/firefox/firefox"),
            version="148.0",
            profile_path=None,
            start_command=None,
            domains=[],
            purpose=None,
            risk_hints=[],
        ),
        builder.DiscoveredContainer(
            name="firefox-gmail",
            root_dir=Path("/tmp/firefox-gmail"),
            binary_path=Path("/tmp/firefox-gmail/firefox/firefox"),
            version="148.0",
            profile_path=None,
            start_command=None,
            domains=[],
            purpose=None,
            risk_hints=[],
        ),
    ]
    specs = [
        builder.ContainerSpec(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            allowed_domains=["github.com"],
            source_firefox_dir=None,
            homepage_url="https://github.com",
            menu_name="NetMon Secure Browser – GitHub",
        ),
        builder.ContainerSpec(
            name="firefox-OpenAI",
            path=Path("/tmp/firefox-OpenAI"),
            allowed_domains=["openai.com"],
            source_firefox_dir=None,
        ),
    ]

    filtered_containers, filtered_specs = builder.filter_by_only(
        containers, specs, "firefox-GitHub"
    )

    assert filtered_containers == []
    assert [spec.name for spec in filtered_specs] == ["firefox-GitHub"]


def test_filter_by_only_rejects_unknown_container_name() -> None:
    try:
        builder.filter_by_only([], [], "firefox-Unknown")
    except ValueError as exc:
        assert "Unbekannter Containername" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown container name")


def test_build_apply_plan_shows_menu_entry(tmp_path: Path) -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=tmp_path / "source",
        menu_name="NetMon Secure Browser – GitHub",
    )

    lines = builder.build_apply_plan([spec], [], tmp_path / "applications")

    rendered = "\n".join(lines)
    assert "Menueeintrag:" in rendered
    assert "netmon-secure-browser-firefox-github.desktop" in rendered


def test_apply_creates_menu_desktop_file(tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=source_dir,
        homepage_url="https://github.com",
        new_tab_url="about:blank",
        menu_name="NetMon Secure Browser – GitHub",
    )

    menu_entry_path = builder.create_container(spec, applications_dir)

    assert menu_entry_path == (
        applications_dir / "netmon-secure-browser-firefox-github.desktop"
    )
    assert menu_entry_path.exists()
    content = menu_entry_path.read_text(encoding="utf-8")
    assert "Name=NetMon Secure Browser – GitHub" in content
    assert f"Exec={spec.path / 'start.sh'}" in content
    assert "Categories=Network;Security;" in content


def test_existing_menu_entry_is_backed_up_before_overwrite(tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    menu_entry_path = applications_dir / "netmon-secure-browser-firefox-github.desktop"
    applications_dir.mkdir(parents=True)
    menu_entry_path.write_text("old desktop entry", encoding="utf-8")
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=source_dir,
        menu_name="NetMon Secure Browser – GitHub",
    )

    builder.create_container(spec, applications_dir)

    backups = list(
        (applications_dir / "browser-container-builder-backups").glob(
            "*/netmon-secure-browser-firefox-github.desktop"
        )
    )
    assert backups
    assert backups[0].read_text(encoding="utf-8") == "old desktop entry"
    assert "old desktop entry" not in menu_entry_path.read_text(encoding="utf-8")


def test_only_limits_menu_entry_in_main(tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    config_path = tmp_path / "containers.json"
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"
    config_path.write_text(
        (
            "{\n"
            f'  "default_source_firefox_dir": "{source_dir}",\n'
            '  "containers": [\n'
            '    {\n'
            '      "name": "firefox-GitHub",\n'
            f'      "path": "{tmp_path / "firefox-GitHub"}",\n'
            '      "allowed_domains": ["github.com"],\n'
            '      "menu_name": "NetMon Secure Browser – GitHub"\n'
            "    },\n"
            '    {\n'
            '      "name": "firefox-OpenAI",\n'
            f'      "path": "{tmp_path / "firefox-OpenAI"}",\n'
            '      "allowed_domains": ["openai.com"],\n'
            '      "menu_name": "NetMon Secure Browser – OpenAI"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--config",
            str(config_path),
            "--inventory",
            str(inventory_path),
            "--only",
            "firefox-GitHub",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert (
        applications_dir / "netmon-secure-browser-firefox-github.desktop"
    ).exists()
    assert not (
        applications_dir / "netmon-secure-browser-firefox-openai.desktop"
    ).exists()
