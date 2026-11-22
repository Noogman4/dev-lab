"""Reject allowlists that could turn a filtered browser into an unrestricted one."""

import json

import pytest

from netmon.core.browser_domains import normalize_allowed_domain
from netmon.modules.secure_browser.manager import SecureBrowserManager
from netmon.modules.secure_browser.models import BrowserContainer
from netmon.modules.secure_browser.service import SecureBrowserService
from tools.secure_browser_manager import browser_container_builder as builder

INVALID_DOMAINS = [
    "*",
    "*.*",
    "*.example.com",
    "*://*/*",
    "https://*",
    "https://*.example.com/",
    "https://%2a/",
    "https://＊/",  # IDNA maps the fullwidth star to an ASCII star.
    "<all_urls>",
    "https://user@example.com/",
    "example.com\\evil",
    "example..com",
    "example.com..",
    "-example.com",
    "example.com:bad",
    "example.com:",
    "example.com:0",
    "example.com:65536",
    "https://exa\nmple.com",
    "https://example.com\t/",
    "ftp://example.com/",
    "https://[::1]/",  # Unsupported by the existing pattern generator.
]


@pytest.mark.parametrize("domain", INVALID_DOMAINS)
def test_shared_parser_rejects_invalid_domains(domain):
    assert normalize_allowed_domain(domain) is None
    assert builder.normalize_allowed_domain(domain) is None
    assert SecureBrowserManager.normalize_allowed_domain(domain) is None
    assert builder.make_match_patterns(domain) == []
    with pytest.raises(ValueError):
        SecureBrowserManager._make_policy_exception_patterns(domain)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (" HTTPS://WWW.Example.COM/login ", "www.example.com"),
        ("https://bücher.de/path", "xn--bcher-kva.de"),
        ("example.com.", "example.com"),
        ("https://example.com:2083/login", "example.com:2083"),
        ("127.0.0.1", "127.0.0.1"),
        ("intranet", "intranet"),
    ],
)
def test_concrete_hosts_and_urls_remain_supported(raw, expected):
    assert normalize_allowed_domain(raw) == expected
    assert builder.normalize_allowed_domain(raw) == expected
    assert SecureBrowserManager.normalize_allowed_domain(raw) == expected


def test_exception_editor_still_rejects_single_label_names():
    with pytest.raises(ValueError):
        SecureBrowserManager._make_policy_exception_patterns("keine-gueltige-domain")


@pytest.mark.parametrize("domains", [["*"], ["example.com", "*"]])
def test_invalid_config_and_form_allowlists_fail_in_full(tmp_path, domains):
    with pytest.raises(ValueError):
        builder.validate_config_payload(
            {"containers": [{"name": "firefox-Test", "allowed_domains": domains}]},
            tmp_path,
        )
    manager = SecureBrowserManager()
    with pytest.raises(ValueError):
        manager._resolve_create_inputs(
            "firefox-Test", "https://example.com", ",".join(domains), "", "", ""
        )


@pytest.mark.parametrize(
    "host", ["trusted.github.io", "www.trusted.github.io", "login.example.co.uk"]
)
def test_new_profile_only_allows_the_start_host_and_explicit_additions(tmp_path, host):
    manager = SecureBrowserManager()
    start_url = f"https://{host}"
    defaults = manager.derive_create_defaults(start_url)
    assert defaults["allowed_domains"] == [host]
    resolved = manager._resolve_create_inputs(
        "", start_url, f"{host}, accounts.example.com", "", "", ""
    )
    spec = builder.ContainerSpec(
        "firefox-Test",
        tmp_path,
        resolved["allowed_domains"],
        None,
        homepage_url=start_url,
    )
    website_filter = builder.build_policies_payload(spec)["policies"]["WebsiteFilter"]
    assert website_filter == {
        "Block": ["<all_urls>"],
        "Exceptions": [f"*://{host}/*", "*://accounts.example.com/*"],
    }


def test_invalid_direct_spec_cannot_create_partial_container(tmp_path):
    root = tmp_path / "firefox-Test"
    spec = builder.ContainerSpec("firefox-Test", root, ["*"], tmp_path / "source")
    with pytest.raises(ValueError):
        builder.create_container(spec, tmp_path / "applications")
    assert not root.exists()
    assert not (tmp_path / "applications").exists()


def test_generated_policies_cannot_gain_a_global_exception(tmp_path, monkeypatch):
    spec = builder.ContainerSpec("firefox-Test", tmp_path, ["example.com"], None)
    monkeypatch.setattr(builder, "make_match_patterns", lambda domain: ["*://*/*"])
    with pytest.raises(ValueError):
        builder.build_policies_payload(spec)


@pytest.mark.parametrize(
    "pattern",
    [
        "*://*/*",
        "http://*/*",
        "https://*/*",
        "*://*.*/*",
        "<all_urls>",
        "*://*.*/x*",
        "*://example.*/*",
        "*://%2a/*",
        "*://＊/*",
        "*://example.com@*/*",
        "*://example.com\n/*",
        42,
    ],
)
def test_policy_editor_and_append_reject_unsafe_existing_exceptions(tmp_path, pattern):
    root = tmp_path / "container"
    runtime = root / "firefox" / "distribution" / "policies.json"
    runtime.parent.mkdir(parents=True)
    source = root / "policies.json"
    for path in (source, runtime):
        path.write_text('{"policies": {}}\n')
    container = BrowserContainer(
        "firefox-Test", root, root / "firefox/firefox", root / "profile", ""
    )
    payload = json.dumps(
        {
            "policies": {
                "WebsiteFilter": {"Block": ["<all_urls>"], "Exceptions": [pattern]}
            }
        }
    )
    with pytest.raises(ValueError):
        SecureBrowserService().save_policy_json(container, payload)
    for path in (source, runtime):
        assert path.read_text() == '{"policies": {}}\n'
    assert not (root / "backups").exists()
    with pytest.raises(ValueError):
        SecureBrowserManager().append_policy_exception_json(payload, "example.com")


def test_generated_and_appended_exceptions_stay_scoped(tmp_path):
    spec = builder.ContainerSpec("firefox-Test", tmp_path, ["www.example.com"], None)
    payload = builder.build_policies_payload(spec)
    website_filter = payload["policies"]["WebsiteFilter"]
    assert website_filter["Block"] == ["<all_urls>"]
    assert website_filter["Exceptions"] == ["*://www.example.com/*"]
    manager = SecureBrowserManager()
    rendered = manager.append_policy_exception_json(
        json.dumps(payload), "www.example.com"
    )
    rendered = manager.append_policy_exception_json(
        rendered, "https://bücher.de:2083/mail"
    )
    assert json.loads(rendered)["policies"]["WebsiteFilter"]["Exceptions"] == [
        "*://www.example.com/*",
        "https://xn--bcher-kva.de:2083/mail*",
    ]


@pytest.mark.parametrize("legacy_wildcard", [False, True])
def test_inventory_flags_broad_saved_domain_rules_without_rewriting(
    tmp_path, legacy_wildcard
):
    container = BrowserContainer(
        "firefox-Test", tmp_path, tmp_path / "firefox/firefox", tmp_path / "profile", ""
    )
    policy = tmp_path / "firefox/distribution/policies.json"
    policy.parent.mkdir(parents=True)
    pattern = "*://*.github.io/*" if legacy_wildcard else "*://trusted.github.io/*"
    original = json.dumps({"policies": {"WebsiteFilter": {"Exceptions": [pattern]}}})
    policy.write_text(original)

    hints = SecureBrowserService().derive_risk_hints(container)

    assert any("Subdomain-Gruppen" in hint for hint in hints) is legacy_wildcard
    assert policy.read_text() == original
    assert not (tmp_path / "policies.json").exists()


def test_explicit_compatible_profile_remains_available(tmp_path):
    spec = builder.ContainerSpec(
        "firefox-Test", tmp_path, ["example.com"], None, security_profile="compatible"
    )
    assert "WebsiteFilter" not in builder.build_policies_payload(spec)["policies"]
