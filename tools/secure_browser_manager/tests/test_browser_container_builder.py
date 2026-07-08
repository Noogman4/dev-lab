import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import browser_container_builder as builder


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
    b"\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

ICO_BYTES = b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x00\x00\x20\x00"
ICO_WITH_PNG_BYTES = (
    b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x00\x00\x20\x00"
    b"\x43\x00\x00\x00\x16\x00\x00\x00"
    + PNG_BYTES
)


def make_firefox_source_tree(base_dir: Path) -> Path:
    source_dir = base_dir / "firefox-source"
    icon_dir = source_dir / "browser" / "chrome" / "icons" / "default"
    icon_dir.mkdir(parents=True)
    firefox_binary = source_dir / "firefox"
    firefox_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(firefox_binary, 0o755)
    (icon_dir / "default128.png").write_text("png", encoding="utf-8")
    return source_dir


def make_existing_container(
    base_dir: Path,
    name: str,
    with_start_script: bool = False,
    with_launcher: bool = False,
    external_profile: Path | None = None,
    domains: list[str] | None = None,
) -> Path:
    root_dir = base_dir / name
    firefox_dir = root_dir / "firefox"
    icon_dir = firefox_dir / "browser" / "chrome" / "icons" / "default"
    profile_dir = root_dir / "profile"
    icon_dir.mkdir(parents=True)
    profile_dir.mkdir(parents=True)
    firefox_binary = firefox_dir / "firefox"
    firefox_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(firefox_binary, 0o755)
    (icon_dir / "default128.png").write_text("png", encoding="utf-8")
    (profile_dir / "prefs.js").write_text('// prefs\n', encoding="utf-8")
    if domains:
        homepage = f"https://{domains[0]}"
        (root_dir / "user.js").write_text(
            (
                f'user_pref("browser.startup.homepage", "{homepage}");\n'
                + "\n".join(
                    f'// allowed domain: https://{domain}/' for domain in domains
                )
                + "\n"
            ),
            encoding="utf-8",
        )
        (root_dir / "policies.json").write_text(
            json.dumps(
                {
                    "policies": {
                        "WebsiteFilter": {
                            "Block": ["<all_urls>"],
                            "Exceptions": [f"*://{domain}/*" for domain in domains],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
    if with_start_script:
        profile_arg = external_profile or profile_dir
        (root_dir / "start.sh").write_text(
            (
                "#!/usr/bin/env bash\n"
                f'exec "$PWD/firefox/firefox" --no-remote --profile "{profile_arg}" "$@"\n'
            ),
            encoding="utf-8",
        )
    if with_launcher:
        (root_dir / "launcher.desktop").write_text("existing launcher", encoding="utf-8")
    return root_dir


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
                "icon_mode": "favicon",
            }
        ]
    }

    specs = builder.validate_config_payload(payload, base_dir)

    assert specs[0].homepage_url == "https://github.com"
    assert specs[0].new_tab_url == "about:blank"
    assert specs[0].menu_name == "NetMon Secure Browser – GitHub"
    assert specs[0].icon_mode == "favicon"


def test_validate_config_payload_rejects_path_traversal_name() -> None:
    base_dir = Path("/tmp/example")
    payload = {
        "containers": [
            {
                "name": "../../../../.config/autostart/x",
                "allowed_domains": ["github.com"],
            }
        ]
    }

    import pytest

    with pytest.raises(ValueError):
        builder.validate_config_payload(payload, base_dir)


def test_validate_config_payload_rejects_dot_and_dotdot_names() -> None:
    base_dir = Path("/tmp/example")
    import pytest

    for bad_name in (".", ".."):
        payload = {
            "containers": [
                {
                    "name": bad_name,
                    "allowed_domains": ["github.com"],
                }
            ]
        }
        with pytest.raises(ValueError, match="'\\.' oder '\\.\\.'"):
            builder.validate_config_payload(payload, base_dir)


def test_fetch_url_rejects_non_http_schemes() -> None:
    import pytest

    for bad_url in (
        "file:///etc/passwd",
        "ftp://example.com/x",
        "gopher://example.com/",
        "/etc/passwd",
    ):
        with pytest.raises(ValueError, match="http/https"):
            builder.fetch_url(bad_url)


def test_build_policies_payload_blocks_all_and_allows_domains() -> None:
    spec = builder.ContainerSpec(
        name="firefox-OpenAI",
        path=Path("/tmp/firefox-OpenAI"),
        allowed_domains=[
            "openai.com",
            "platform.openai.com",
            "oaistatic.com",
            "oaiusercontent.com",
            "netmonroots.com:2083",
        ],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://chatgpt.com",
        new_tab_url="about:blank",
    )

    payload = builder.build_policies_payload(spec)
    homepage = payload["policies"]["Homepage"]
    website_filter = payload["policies"]["WebsiteFilter"]

    assert homepage["URL"] == "https://chatgpt.com"
    assert homepage["StartPage"] == "homepage"
    assert payload["policies"]["DisableMasterPasswordCreation"] is False
    assert payload["policies"]["OfferToSaveLogins"] is True
    assert payload["policies"]["PasswordManagerEnabled"] is True
    assert payload["policies"]["OverrideFirstRunPage"] == ""
    assert payload["policies"]["OverridePostUpdatePage"] == ""
    assert website_filter["Block"] == ["<all_urls>"]
    assert "*://openai.com/*" in website_filter["Exceptions"]
    assert "*://*.openai.com/*" in website_filter["Exceptions"]
    assert "*://platform.openai.com/*" in website_filter["Exceptions"]
    assert "*://*.platform.openai.com/*" in website_filter["Exceptions"]
    assert "*://oaistatic.com/*" in website_filter["Exceptions"]
    assert "*://*.oaistatic.com/*" in website_filter["Exceptions"]
    assert "*://oaiusercontent.com/*" in website_filter["Exceptions"]
    assert "*://*.oaiusercontent.com/*" in website_filter["Exceptions"]
    assert "https://netmonroots.com/*" in website_filter["Exceptions"]


def test_make_match_patterns_for_www_domain_includes_base_and_subdomains() -> None:
    patterns = builder.make_match_patterns("www.netflix.com")

    assert "*://www.netflix.com/*" in patterns
    assert "*://netflix.com/*" in patterns
    assert "*://*.netflix.com/*" in patterns


def test_make_match_patterns_normalizes_url_like_domain_input() -> None:
    patterns = builder.make_match_patterns("https://hs21.name.tools:2083/login")

    assert patterns == ["https://hs21.name.tools/*"]


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

    assert 'user_pref("browser.aboutwelcome.enabled", false);' in content
    assert 'user_pref("browser.startup.homepage", "https://github.com");' in content
    assert 'user_pref("browser.newtabpage.enabled", false);' in content
    assert 'user_pref("browser.newtab.url", "about:blank");' in content
    assert 'user_pref("signon.autofillForms", true);' in content
    assert 'user_pref("signon.rememberSignons", true);' in content
    assert 'user_pref("startup.homepage_welcome_url", "");' in content
    assert 'user_pref("startup.homepage_welcome_url.additional", "");' in content


def test_build_user_js_content_strict_profile_disables_password_manager_and_keeps_no_cookies() -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        allowed_domains=["github.com"],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://github.com",
        new_tab_url="about:blank",
        security_profile="strict",
    )

    content = builder.build_user_js_content(spec)

    assert '// Security profile: strict' in content
    assert 'user_pref("signon.rememberSignons", false);' in content
    assert 'user_pref("network.cookie.lifetimePolicy", 2);' in content
    assert 'user_pref("privacy.clearOnShutdown.cookies", true);' in content


def test_build_policies_payload_compatible_profile_disables_website_filter() -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        allowed_domains=["github.com"],
        source_firefox_dir=Path("/tmp/source"),
        homepage_url="https://github.com",
        security_profile="compatible",
    )

    payload = builder.build_policies_payload(spec)

    assert "WebsiteFilter" not in payload["policies"]
    assert payload["policies"]["PasswordManagerEnabled"] is True
    assert payload["_builder_metadata"]["security_profile"] == "compatible"


def test_validate_config_payload_reads_security_options() -> None:
    base_dir = Path("/tmp/example")
    payload = {
        "containers": [
            {
                "name": "firefox-GitHub",
                "allowed_domains": ["github.com"],
                "security_profile": "strict",
                "allow_password_manager": False,
                "keep_cookies": False,
                "enable_website_filter": True,
            }
        ]
    }

    specs = builder.validate_config_payload(payload, base_dir)

    assert specs[0].security_profile == "strict"
    assert specs[0].allow_password_manager is False
    assert specs[0].keep_cookies is False
    assert specs[0].enable_website_filter is True


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
    assert "Passwortmanager bleibt pro Container aktiv" in readme
    assert "netmon-secure-browser-firefox-github.desktop" in readme


def test_validate_config_payload_normalizes_url_like_allowed_domains() -> None:
    base_dir = Path("/tmp/example")
    payload = {
        "containers": [
            {
                "name": "firefox-Proton",
                "allowed_domains": [
                    "https://proton.me/",
                    "https://account.proton.me/login",
                ],
            }
        ]
    }

    specs = builder.validate_config_payload(payload, base_dir)

    assert specs[0].allowed_domains == ["proton.me", "account.proton.me"]


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
    assert "StartupWMClass=firefox" in content
    assert "Name=NetMon Secure Browser – GitHub" in content
    assert (
        'Exec=env BAMF_DESKTOP_FILE_HINT="/home/happy/.local/share/applications/'
        'netmon-secure-browser-firefox-github.desktop" "/tmp/firefox-GitHub/start.sh"'
        in content
    )


def test_get_default_menu_name_supports_new_labels() -> None:
    amazon = builder.ContainerSpec(
        name="firefox-Amazon",
        path=Path("/tmp/firefox-Amazon"),
        allowed_domains=["amazon.de"],
        source_firefox_dir=None,
    )
    sparkasse = builder.ContainerSpec(
        name="firefox-SparkasseUlm",
        path=Path("/tmp/firefox-SparkasseUlm"),
        allowed_domains=["sparkasse-ulm.de"],
        source_firefox_dir=None,
    )

    assert builder.get_default_menu_name(amazon) == "NetMon Secure Browser – Amazon"
    assert (
        builder.get_default_menu_name(sparkasse)
        == "NetMon Secure Browser – Sparkasse Ulm"
    )


def test_score_profile_match_counts_expected_domain_hits() -> None:
    profile = builder.FirefoxProfile(
        path=Path("/tmp/profile"),
        domains=["chatgpt.com", "cdn.openai.com", "oaistatic.com"],
        sources=["places.sqlite"],
    )

    score, matched_domains = builder.score_profile_match(
        profile, ["chatgpt.com", "openai.com", "oaistatic.com"]
    )

    assert score == 3
    assert matched_domains == ["chatgpt.com", "openai.com", "oaistatic.com"]


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


def test_parse_args_accepts_refresh_existing_option() -> None:
    args = builder.parse_args(["--refresh-existing", "--only", "Sparkasse"])

    assert args.refresh_existing is True
    assert args.only == "Sparkasse"


def test_parse_args_accepts_repair_policy_option() -> None:
    args = builder.parse_args(["--repair-policy", "--only", "Netflix"])

    assert args.repair_policy is True
    assert args.only == "Netflix"


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
    assert "Favicon-URL:" in rendered


def test_dry_run_does_not_download_favicon(tmp_path: Path, monkeypatch) -> None:
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=tmp_path / "source",
        homepage_url="https://github.com",
        icon_mode="favicon",
    )
    called = {"count": 0}

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        called["count"] += 1
        return b"", None

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    lines = builder.build_apply_plan([spec], [], tmp_path / "applications")

    assert called["count"] == 0
    assert "https://github.com/favicon.ico" in "\n".join(lines)


def test_apply_downloads_and_stores_favicon(monkeypatch, tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=source_dir,
        homepage_url="https://github.com",
        icon_mode="favicon",
        menu_name="NetMon Secure Browser – GitHub",
    )

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://github.com":
            return (
                b'<html><head><link rel="icon" href="/favicon.png"></head></html>',
                "text/html",
            )
        if url == "https://github.com/favicon.png":
            return (PNG_BYTES, "image/png")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    menu_entry_path = builder.create_container(spec, applications_dir)

    icon_path = spec.path / "icons" / "favicon.png"
    assert icon_path.exists()
    assert icon_path.read_bytes() == PNG_BYTES
    assert f"Icon={icon_path}" in (spec.path / "launcher.desktop").read_text(encoding="utf-8")
    assert f"Icon={icon_path}" in menu_entry_path.read_text(encoding="utf-8")


def test_extract_icon_links_ignores_mask_icon_and_prefers_png() -> None:
    html = """
    <html>
      <head>
        <link rel="mask-icon" href="/pinned-octocat.svg">
        <link rel="icon" href="/favicon.png">
        <link rel="apple-touch-icon" href="/apple-touch-icon.png">
      </head>
    </html>
    """

    links = builder.extract_icon_links(html, "https://github.com")

    assert links[0] == "https://github.com/favicon.png"
    assert "https://github.com/favicon.png" in links
    assert "https://github.com/pinned-octocat.svg" not in links


def test_favicon_fallback_uses_default_icon(monkeypatch, tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=source_dir,
        homepage_url="https://github.com",
        icon_mode="favicon",
        menu_name="NetMon Secure Browser – GitHub",
    )

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    menu_entry_path = builder.create_container(spec, applications_dir)

    assert not (spec.path / "icons").exists()
    assert "Icon=firefox" in menu_entry_path.read_text(encoding="utf-8")


def test_invalid_png_payload_falls_back_to_default_icon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="Sparkasse",
        path=tmp_path / "Sparkasse",
        allowed_domains=["www.sparkasse-ulm.de"],
        source_firefox_dir=source_dir,
        homepage_url="https://www.sparkasse-ulm.de",
        icon_mode="favicon",
        menu_name="Sparkasse",
    )

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://www.sparkasse-ulm.de":
            return (
                b'<html><head><link rel="icon" href="/favicon.png"></head></html>',
                "text/html",
            )
        if url == "https://www.sparkasse-ulm.de/favicon.png":
            return (b"not-a-real-png", "image/png")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    menu_entry_path = builder.create_container(spec, applications_dir)

    assert not (spec.path / "icons").exists()
    assert "Icon=firefox" in menu_entry_path.read_text(encoding="utf-8")


def test_invalid_first_icon_tries_next_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="Sparkasse",
        path=tmp_path / "Sparkasse",
        allowed_domains=["www.sparkasse-ulm.de"],
        source_firefox_dir=source_dir,
        homepage_url="https://www.sparkasse-ulm.de",
        icon_mode="favicon",
        menu_name="Sparkasse",
    )

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://www.sparkasse-ulm.de":
            return (
                (
                    b'<html><head>'
                    b'<link rel="icon" href="/favicon.png">'
                    b'<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
                    b"</head></html>"
                ),
                "text/html",
            )
        if url == "https://www.sparkasse-ulm.de/favicon.png":
            return (b"not-a-real-png", "image/png")
        if url == "https://www.sparkasse-ulm.de/apple-touch-icon.png":
            return (PNG_BYTES, "image/png")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    menu_entry_path = builder.create_container(spec, applications_dir)

    icon_path = spec.path / "icons" / "favicon.png"
    assert icon_path.exists()
    assert icon_path.read_bytes() == PNG_BYTES
    assert f"Icon={icon_path}" in menu_entry_path.read_text(encoding="utf-8")


def test_existing_icon_is_backed_up_before_replace(monkeypatch, tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    spec = builder.ContainerSpec(
        name="firefox-GitHub",
        path=tmp_path / "firefox-GitHub",
        allowed_domains=["github.com"],
        source_firefox_dir=source_dir,
        homepage_url="https://github.com",
        icon_mode="favicon",
        menu_name="NetMon Secure Browser – GitHub",
    )
    spec.path.mkdir(parents=True)
    icon_dir = spec.path / "icons"
    icon_dir.mkdir()
    existing_icon = icon_dir / "favicon.png"
    existing_icon.write_bytes(b"oldpng")

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://github.com":
            return (
                b'<html><head><link rel="icon" href="/favicon.ico"></head></html>',
                "text/html",
            )
        if url == "https://github.com/favicon.ico":
            return (ICO_WITH_PNG_BYTES, "image/x-icon")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    icon_path, _warning = builder.prepare_container_icon(spec)

    backups = list((icon_dir / "browser-container-builder-backups").glob("*/favicon.png"))
    assert backups
    assert backups[0].read_bytes() == b"oldpng"
    assert Path(icon_path).suffix == ".png"
    assert Path(icon_path).read_bytes() == PNG_BYTES


def test_ico_with_embedded_png_is_saved_as_png(monkeypatch, tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    spec = builder.ContainerSpec(
        name="Sparkasse",
        path=tmp_path / "Sparkasse",
        allowed_domains=["www.sparkasse-ulm.de"],
        source_firefox_dir=source_dir,
        homepage_url="https://www.sparkasse-ulm.de",
        icon_mode="favicon",
        menu_name="Sparkasse",
    )

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://www.sparkasse-ulm.de":
            return (b"<html><head></head></html>", "text/html")
        if url == "https://www.sparkasse-ulm.de/favicon.ico":
            return (ICO_WITH_PNG_BYTES, "image/x-icon")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    menu_entry_path = builder.create_container(spec, applications_dir)

    icon_path = spec.path / "icons" / "favicon.png"
    assert icon_path.exists()
    assert icon_path.read_bytes() == PNG_BYTES
    assert f"Icon={icon_path}" in menu_entry_path.read_text(encoding="utf-8")


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
    assert (
        f'Exec=env BAMF_DESKTOP_FILE_HINT="{menu_entry_path}" "{spec.path / "start.sh"}"'
        in content
    )
    assert "Categories=Network;Security;" in content
    assert "StartupWMClass=firefox" in content
    assert os.access(menu_entry_path, os.X_OK)
    assert os.access(spec.path / "launcher.desktop", os.X_OK)


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

    assert "old desktop entry" not in menu_entry_path.read_text(encoding="utf-8")


def test_create_container_removes_conflicting_menu_entry_by_visible_name(
    tmp_path: Path,
) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir(parents=True)
    spec = builder.ContainerSpec(
        name="Sparkasse",
        path=tmp_path / "Sparkasse",
        allowed_domains=["www.sparkasse-ulm.de"],
        source_firefox_dir=source_dir,
        homepage_url="https://www.sparkasse-ulm.de",
        menu_name="NetMon Secure Browser – Sparkasse",
    )
    old_entry = applications_dir / "netmon-secure-browser-firefox-sparkasseulm.desktop"
    old_entry.write_text(
        (
            "[Desktop Entry]\n"
            "Version=1.0\n"
            "Type=Application\n"
            "Name=NetMon Secure Browser – Sparkasse\n"
            f"Exec={spec.path / 'start.sh'}\n"
            "Icon=/tmp/old-sparkasse/icon.png\n"
            "Terminal=false\n"
        ),
        encoding="utf-8",
    )

    menu_entry_path = builder.create_container(spec, applications_dir)

    assert menu_entry_path == applications_dir / "netmon-secure-browser-sparkasse.desktop"
    assert menu_entry_path.exists()
    assert not old_entry.exists()
    assert (
        "Name=NetMon Secure Browser – Sparkasse"
        in menu_entry_path.read_text(encoding="utf-8")
    )


def test_create_container_removes_conflicting_non_managed_desktop_entry(
    tmp_path: Path,
) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir(parents=True)
    spec = builder.ContainerSpec(
        name="Sparkasse",
        path=tmp_path / "Sparkasse",
        allowed_domains=["www.sparkasse-ulm.de"],
        source_firefox_dir=source_dir,
        homepage_url="https://www.sparkasse-ulm.de",
        menu_name="NetMon Secure Browser – Sparkasse",
    )
    legacy_entry = applications_dir / "Sparkasse.desktop"
    legacy_entry.write_text(
        (
            "[Desktop Entry]\n"
            "Version=1.0\n"
            "Type=Application\n"
            "Name=Sparkasse\n"
            f"Exec={spec.path / 'start.sh'}\n"
            "Icon=/tmp/legacy.png\n"
            "Terminal=false\n"
        ),
        encoding="utf-8",
    )

    builder.create_container(spec, applications_dir)

    assert not legacy_entry.exists()


def test_register_existing_candidates_include_default_containers() -> None:
    container = builder.DiscoveredContainer(
        name="firefox-GitHub",
        root_dir=Path("/tmp/firefox-GitHub"),
        binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
        version="1.0",
        profile_path=None,
        start_command=None,
        domains=["github.com"],
        purpose=None,
        risk_hints=[],
    )

    candidates = builder.get_register_existing_candidates([container])

    assert [item.name for item in candidates] == ["firefox-GitHub"]


def test_parse_desktop_exec_target_supports_env_bamf_hint(tmp_path: Path) -> None:
    desktop_path = tmp_path / "sparkasse.desktop"
    desktop_path.write_text(
        (
            "[Desktop Entry]\n"
            'Exec=env BAMF_DESKTOP_FILE_HINT="/tmp/sparkasse.desktop" "/tmp/Sparkasse/start.sh"\n'
        ),
        encoding="utf-8",
    )

    target = builder.parse_desktop_exec_target(desktop_path)

    assert target == Path("/tmp/Sparkasse/start.sh")


def test_register_existing_candidates_include_custom_container_names() -> None:
    container = builder.DiscoveredContainer(
        name="Sparkasse",
        root_dir=Path("/tmp/Sparkasse"),
        binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
        version="1.0",
        profile_path=None,
        start_command=None,
        domains=["www.sparkasse-ulm.de"],
        purpose=None,
        risk_hints=[],
    )

    candidates = builder.get_register_existing_candidates([container])

    assert [item.name for item in candidates] == ["Sparkasse"]


def test_build_repair_policy_spec_uses_known_bundle_for_custom_github_name() -> None:
    container = builder.DiscoveredContainer(
        name="GitHub",
        root_dir=Path("/tmp/GitHub"),
        binary_path=Path("/tmp/GitHub/firefox/firefox"),
        version="1.0",
        profile_path=None,
        start_command=None,
        domains=["www.github.com"],
        purpose="GitHub",
        risk_hints=[],
    )

    spec = builder.build_repair_policy_spec(container)

    assert spec.allowed_domains == [
        "www.github.com",
        "github.com",
        "githubusercontent.com",
        "githubassets.com",
    ]


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


def test_first_start_uses_configured_homepage(tmp_path: Path) -> None:
    source_dir = make_firefox_source_tree(tmp_path)
    firefox_binary = source_dir / "firefox"
    output_path = tmp_path / "first-start.json"
    firefox_binary.write_text(
        f"""#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

profile_arg = Path(sys.argv[sys.argv.index("--profile") + 1])
policies_path = Path(__file__).resolve().parent / "distribution" / "policies.json"
user_js_path = profile_arg / "user.js"

policies = json.loads(policies_path.read_text(encoding="utf-8"))
user_js = user_js_path.read_text(encoding="utf-8")

def find_pref(name: str) -> str | None:
    prefix = f'user_pref("{{name}}", '
    for line in user_js.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix):-2]
            return value.strip('"')
    return None

result = {{
    "argv": sys.argv[1:],
    "homepage_policy": policies["policies"]["Homepage"]["URL"],
    "override_first_run_page": policies["policies"]["OverrideFirstRunPage"],
    "override_post_update_page": policies["policies"]["OverridePostUpdatePage"],
    "user_homepage": find_pref("browser.startup.homepage"),
    "welcome_url": find_pref("startup.homepage_welcome_url"),
    "welcome_url_additional": find_pref("startup.homepage_welcome_url.additional"),
    "aboutwelcome_enabled": find_pref("browser.aboutwelcome.enabled"),
}}

Path({str(output_path)!r}).write_text(json.dumps(result), encoding="utf-8")
""",
        encoding="utf-8",
    )
    os.chmod(firefox_binary, 0o755)
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

    builder.create_container(spec, applications_dir)
    subprocess.run(
        [str(spec.path / "start.sh")],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["homepage_policy"] == "https://github.com"
    assert result["user_homepage"] == "https://github.com"
    assert result["override_first_run_page"] == ""
    assert result["override_post_update_page"] == ""
    assert result["welcome_url"] == ""
    assert result["welcome_url_additional"] == ""
    assert result["aboutwelcome_enabled"] == "false"


def test_register_existing_dry_run_shows_menu_entry(tmp_path: Path) -> None:
    root_dir = make_existing_container(tmp_path, "firefox-gmail")
    container = builder.discover_container(root_dir / "firefox" / "firefox")

    lines = builder.build_register_existing_plan([container], tmp_path / "applications")

    rendered = "\n".join(lines)
    assert "Menueeintrag:" in rendered
    assert "netmon-secure-browser-firefox-gmail.desktop" in rendered


def test_register_existing_apply_creates_start_launcher_and_menu(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(base_dir, "firefox-gmail")
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--register-existing",
            "--only",
            "firefox-gmail",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    start_script = (root_dir / "start.sh").read_text(encoding="utf-8")
    launcher = (root_dir / "launcher.desktop").read_text(encoding="utf-8")
    menu_entry = (
        applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    ).read_text(encoding="utf-8")
    assert '--profile "' in start_script
    assert "profile" in start_script
    assert "NetMon Secure Browser – Gmail" in launcher
    assert "NetMon Secure Browser – Gmail" in menu_entry
    assert os.access(root_dir / "launcher.desktop", os.X_OK)
    assert os.access(
        applications_dir / "netmon-secure-browser-firefox-gmail.desktop",
        os.X_OK,
    )


def test_register_existing_apply_supports_custom_container_name(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(
        base_dir,
        "Sparkasse",
        domains=["www.sparkasse-ulm.de"],
    )
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--register-existing",
            "--only",
            "Sparkasse",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    launcher = (root_dir / "launcher.desktop").read_text(encoding="utf-8")
    menu_entry = (
        applications_dir / "netmon-secure-browser-sparkasse.desktop"
    ).read_text(encoding="utf-8")
    assert "Name=NetMon Secure Browser – Sparkasse" in launcher
    assert "Name=NetMon Secure Browser – Sparkasse" in menu_entry
    assert (
        f'Exec=env BAMF_DESKTOP_FILE_HINT="{applications_dir / "netmon-secure-browser-sparkasse.desktop"}" '
        f'"{root_dir / "start.sh"}"'
        in menu_entry
    )


def test_refresh_existing_apply_overwrites_launcher_and_menu(tmp_path: Path, monkeypatch) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(
        base_dir,
        "Sparkasse",
        with_start_script=True,
        with_launcher=True,
        domains=["www.sparkasse-ulm.de"],
    )
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"
    (root_dir / "start.sh").write_text("old start", encoding="utf-8")
    (root_dir / "launcher.desktop").write_text("old launcher", encoding="utf-8")
    applications_dir.mkdir(parents=True)
    menu_entry_path = applications_dir / "netmon-secure-browser-sparkasse.desktop"
    menu_entry_path.write_text("old menu", encoding="utf-8")

    def fake_fetch_url(url: str) -> tuple[bytes, str | None]:
        if url == "https://www.sparkasse-ulm.de":
            return (b"<html><head></head></html>", "text/html")
        if url == "https://www.sparkasse-ulm.de/favicon.ico":
            return (ICO_WITH_PNG_BYTES, "image/x-icon")
        raise RuntimeError(url)

    monkeypatch.setattr(builder, "fetch_url", fake_fetch_url)

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--refresh-existing",
            "--only",
            "Sparkasse",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert "old start" not in (root_dir / "start.sh").read_text(encoding="utf-8")
    assert "old launcher" not in (root_dir / "launcher.desktop").read_text(encoding="utf-8")
    updated_menu = menu_entry_path.read_text(encoding="utf-8")
    assert "old menu" not in updated_menu
    assert f"Icon={root_dir / 'icons' / 'favicon.png'}" in updated_menu
    assert f"Icon={root_dir / 'icons' / 'favicon.png'}" in (
        root_dir / "launcher.desktop"
    ).read_text(encoding="utf-8")


def test_repair_policy_apply_updates_existing_policy_and_user_js(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(
        base_dir,
        "Netflix",
        with_start_script=True,
        domains=["www.netflix.com"],
    )
    inventory_path = tmp_path / "inventory.md"
    (root_dir / "policies.json").write_text("{}", encoding="utf-8")
    (root_dir / "user.js").write_text("// old\n", encoding="utf-8")
    (root_dir / "profile" / "user.js").write_text("// old profile\n", encoding="utf-8")

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--repair-policy",
            "--only",
            "Netflix",
            "--apply",
        ],
        applications_dir=tmp_path / "applications",
    )

    assert exit_code == 0
    policies = json.loads((root_dir / "policies.json").read_text(encoding="utf-8"))
    exceptions = policies["policies"]["WebsiteFilter"]["Exceptions"]
    assert "*://www.netflix.com/*" in exceptions
    assert "*://netflix.com/*" in exceptions
    assert "*://*.netflix.com/*" in exceptions
    assert "*://nflxvideo.net/*" in exceptions
    assert "*://*.nflxvideo.net/*" in exceptions
    assert 'user_pref("browser.startup.homepage", "https://netflix.com");' in (
        root_dir / "user.js"
    ).read_text(encoding="utf-8")


def test_cleanup_menu_detects_duplicate_visible_names(tmp_path: Path) -> None:
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir()
    first = applications_dir / "netmon-secure-browser-sparkasse.desktop"
    second = applications_dir / "netmon-secure-browser-firefox-sparkasseulm.desktop"
    content = (
        "[Desktop Entry]\n"
        "Name=NetMon Secure Browser – Sparkasse\n"
        "Exec=/tmp/sparkasse/start.sh\n"
    )
    first.write_text(content, encoding="utf-8")
    second.write_text(content.replace("/tmp/sparkasse/", "/tmp/sparkasse2/"), encoding="utf-8")

    lines, removable = builder.build_cleanup_menu_plan(applications_dir)

    rendered = "\n".join(lines)
    assert "doppelt" in rendered
    assert second in [entry.path for entry in removable]


def test_register_existing_does_not_overwrite_existing_start_or_launcher(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(
        base_dir,
        "firefox-youtube",
        with_start_script=True,
        with_launcher=True,
    )
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--register-existing",
            "--only",
            "firefox-youtube",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert '--profile "' in (root_dir / "start.sh").read_text(encoding="utf-8")
    assert (root_dir / "launcher.desktop").read_text(encoding="utf-8") == "existing launcher"


def test_register_existing_overwrites_existing_menu_entry(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    make_existing_container(base_dir, "firefox-chatgpt")
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir(parents=True)
    menu_entry_path = applications_dir / "netmon-secure-browser-firefox-chatgpt.desktop"
    menu_entry_path.write_text("old menu", encoding="utf-8")

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--register-existing",
            "--only",
            "firefox-chatgpt",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    updated = menu_entry_path.read_text(encoding="utf-8")
    assert "old menu" not in updated
    assert "Exec=" in updated


def test_register_existing_only_limits_menu_entry(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    make_existing_container(base_dir, "firefox-gmail")
    make_existing_container(base_dir, "firefox-youtube")
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--register-existing",
            "--only",
            "firefox-gmail",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert (
        applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    ).exists()
    assert not (
        applications_dir / "netmon-secure-browser-firefox-youtube.desktop"
    ).exists()


def test_list_installed_detects_container_and_menu_entry(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(base_dir, "firefox-gmail", with_launcher=True)
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir()
    menu_entry = applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    menu_entry.write_text(
        f"[Desktop Entry]\nExec={root_dir / 'start.sh'}\n",
        encoding="utf-8",
    )

    report = builder.build_list_installed_report(
        [builder.discover_container(root_dir / "firefox" / "firefox")],
        applications_dir,
    )

    rendered = "\n".join(report)
    assert "firefox-gmail" in rendered
    assert "Menueeintraege:" in rendered


def test_cleanup_menu_detects_orphaned_entry(tmp_path: Path) -> None:
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir()
    orphan = applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    orphan.write_text("[Desktop Entry]\nExec=/missing/start.sh\n", encoding="utf-8")

    lines, removable = builder.build_cleanup_menu_plan(applications_dir)

    assert orphan in [entry.path for entry in removable]
    assert "verwaist" in "\n".join(lines)


def test_cleanup_menu_removes_only_with_apply(tmp_path: Path) -> None:
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir()
    orphan = applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    orphan.write_text("[Desktop Entry]\nExec=/missing/start.sh\n", encoding="utf-8")
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    inventory_path = tmp_path / "inventory.md"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--cleanup-menu",
        ],
        applications_dir=applications_dir,
    )
    assert exit_code == 0
    assert orphan.exists()

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--cleanup-menu",
            "--apply",
        ],
        applications_dir=applications_dir,
    )
    assert exit_code == 0
    assert not orphan.exists()


def test_uninstall_dry_run_is_safe(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(base_dir, "firefox-gmail")
    inventory_path = tmp_path / "inventory.md"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--uninstall",
            "firefox-gmail",
        ],
        applications_dir=tmp_path / "applications",
    )

    assert exit_code == 0
    assert root_dir.exists()


def test_uninstall_apply_moves_container_to_uninstalled(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(base_dir, "firefox-gmail")
    inventory_path = tmp_path / "inventory.md"
    applications_dir = tmp_path / "applications"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--uninstall",
            "firefox-gmail",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert not root_dir.exists()
    moved = list(
        (base_dir / "browser-container-builder-uninstalled").glob("*/firefox-gmail")
    )
    assert moved


def test_inventory_skips_uninstalled_backup_tree(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    make_existing_container(base_dir, "firefox-gmail")
    uninstall_root = base_dir / builder.DEFAULT_UNINSTALLED_DIRNAME / "20260705_120000"
    make_existing_container(uninstall_root, "firefox-chatgpt")

    discovered = builder.discover_existing_containers(base_dir)

    assert [container.name for container in discovered] == ["firefox-gmail"]


def test_uninstall_never_deletes_external_profiles(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    external_profile = tmp_path / "external-profile"
    external_profile.mkdir()
    (external_profile / "prefs.js").write_text("// ext\n", encoding="utf-8")
    root_dir = make_existing_container(
        base_dir,
        "firefox-gmail",
        with_start_script=True,
        external_profile=external_profile,
    )
    inventory_path = tmp_path / "inventory.md"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--uninstall",
            "firefox-gmail",
            "--apply",
        ],
        applications_dir=tmp_path / "applications",
    )

    assert exit_code == 0
    assert external_profile.exists()
    assert not root_dir.exists()


def test_uninstall_backs_up_and_removes_menu_entries(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    root_dir = make_existing_container(base_dir, "firefox-gmail")
    applications_dir = tmp_path / "applications"
    applications_dir.mkdir()
    menu_entry = applications_dir / "netmon-secure-browser-firefox-gmail.desktop"
    menu_entry.write_text(
        f"[Desktop Entry]\nExec={root_dir / 'start.sh'}\n",
        encoding="utf-8",
    )
    inventory_path = tmp_path / "inventory.md"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--uninstall",
            "firefox-gmail",
            "--apply",
        ],
        applications_dir=applications_dir,
    )

    assert exit_code == 0
    assert not menu_entry.exists()


def test_uninstall_unknown_container_is_reported(tmp_path: Path) -> None:
    base_dir = tmp_path / "programme"
    base_dir.mkdir()
    inventory_path = tmp_path / "inventory.md"

    exit_code = builder.main(
        [
            "--base-dir",
            str(base_dir),
            "--inventory",
            str(inventory_path),
            "--uninstall",
            "firefox-Unknown",
        ],
        applications_dir=tmp_path / "applications",
    )

    assert exit_code == 1
