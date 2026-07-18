from netmon.services.rkhunter_analysis_service import (
    analyze_rkhunter_output,
    extract_replaced_script_paths,
    extract_warning_command_paths,
)


def _complete_scan(*lines):
    return "\n".join((*lines, "System checks summary", "Possible rootkits: 0"))


def test_expected_configuration_and_developer_changes_are_low_risk():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: File properties have changed: /etc/rkhunter.conf",
            "Warning: File properties have changed: /etc/systemd/resolved.conf",
            "Warning: Hidden file found in VS Code dev-container: /home/demo/.vscode/a",
        ),
        1,
        dpkg_output="??5?????? c /etc/fwupd.conf",
        dpkg_rc=0,
    )

    assert result["risk"] == "low"
    assert {item["code"] for item in result["expected"]} == {
        "configuration_file",
        "developer_environment",
        "dpkg_configuration_file",
    }
    assert result["review"] == []
    assert result["critical"] == []
    assert result["propupd_allowed"] is True


def test_non_whitelisted_etc_conf_change_requires_review_and_blocks_propupd():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: File properties have changed: /etc/cron.d/persist.conf",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "medium"
    assert [item["code"] for item in result["review"]] == ["unclassified_warning"]
    assert result["expected"] == []
    assert result["propupd_allowed"] is False


def test_developer_environment_requires_real_boundary_not_substring_match():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: Hidden file found: /etc/dockerish-malware/payload",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "medium"
    assert [item["code"] for item in result["review"]] == ["hidden_system_file"]
    assert result["expected"] == []
    assert result["propupd_allowed"] is False


def test_negative_rootkit_and_backdoor_messages_are_not_findings():
    result = analyze_rkhunter_output(
        _complete_scan(
            "No rootkits found",
            "Checking for backdoor ports [ None found ]",
            "Suspect files: 0",
        ),
        0,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["findings"] == []
    assert result["risk"] == "low"
    assert result["propupd_allowed"] is True


def test_hidden_system_file_and_local_executable_require_review():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: Hidden file found: /etc/.unknown",
            "Warning: New executable found: /usr/local/bin/mystery",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "medium"
    assert {item["code"] for item in result["review"]} == {
        "hidden_system_file",
        "local_executable",
    }
    assert result["propupd_allowed"] is False


def test_hidden_file_log_evidence_keeps_propupd_locked_until_path_is_reviewed():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Checking for hidden files and directories                [ Warning ]",
            "Suspect files: 1",
            "=== rkhunter log evidence ===",
            "[12:00:00] Warning: Hidden file found: /etc/.java",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "medium"
    assert {item["code"] for item in result["review"]} == {
        "hidden_files_summary",
        "hidden_system_file",
        "suspect_files",
    }
    assert result["propupd_allowed"] is False


def test_known_hidden_system_artifacts_do_not_block_propupd():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Checking for hidden files and directories                [ Warning ]",
            "Suspect files: 1",
            "=== rkhunter log evidence ===",
            "[12:23:57] Warning: Hidden file found: /etc/.resolv.conf.systemd-resolved.bak: ASCII text",
            "[12:23:57] Warning: Hidden file found: /etc/.updated: ASCII text",
            "[12:23:57] Suspect files: 1",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "low"
    assert result["review"] == []
    assert {item["code"] for item in result["expected"]} == {
        "hidden_files_explained",
        "hidden_system_artifact",
    }
    assert result["propupd_allowed"] is True


def test_rootkit_and_modified_sudo_are_critical():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: Rootkit FooKit found",
            "Warning: /usr/bin/sudo has been modified",
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["risk"] == "high"
    assert {item["code"] for item in result["critical"]} == {
        "rootkit",
        "system_program",
    }
    assert result["propupd_allowed"] is False


def test_dpkg_core_program_change_blocks_propupd():
    result = analyze_rkhunter_output(
        _complete_scan(),
        0,
        dpkg_output="..5...... /usr/bin/bash",
        dpkg_rc=0,
    )

    assert result["risk"] == "high"
    assert result["critical"][0]["code"] == "dpkg_system_program"
    assert result["propupd_allowed"] is False


def test_packaged_replaced_script_warning_is_expected_false_positive():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: The command '/usr/bin/lwp-request' has been replaced by a script"
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
        dpkg_owner_output="/usr/bin/lwp-request\t0\tlibwww-perl: /usr/bin/lwp-request",
        file_type_output="/usr/bin/lwp-request\t0\tPerl script text executable",
    )

    assert extract_replaced_script_paths(result["expected"][0]["line"]) == [
        "/usr/bin/lwp-request"
    ]
    assert result["risk"] == "low"
    assert result["review"] == []
    assert result["expected"][0]["code"] == "packaged_script_false_positive"
    assert (
        result["expected"][0]["reason"]
        == "Kein Hinweis auf Manipulation. Wahrscheinlich distributionsbedingter Fehlalarm."
    )
    assert result["propupd_allowed"] is True


def test_packaged_warning_command_is_expected_false_positive_with_evidence():
    result = analyze_rkhunter_output(
        _complete_scan(
            "/usr/bin/lwp-request                                     [ Warning ]"
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
        dpkg_owner_output="/usr/bin/lwp-request\t0\tlibwww-perl: /usr/bin/lwp-request",
        file_type_output="/usr/bin/lwp-request\t0\tPerl script text executable",
    )

    assert extract_warning_command_paths(result["expected"][0]["line"]) == [
        "/usr/bin/lwp-request"
    ]
    assert result["risk"] == "low"
    assert result["review"] == []
    assert result["expected"][0]["code"] == "packaged_script_false_positive"
    assert result["propupd_allowed"] is True


def test_expected_dpkg_permission_noise_does_not_block_propupd():
    result = analyze_rkhunter_output(
        _complete_scan(),
        0,
        dpkg_output="\n".join(
            [
                "missing     /var/lib/polkit-1/localauthority (Keine Berechtigung)",
                "missing     /var/cache/cups/rss (Keine Berechtigung)",
                "missing     /etc/apparmor.d/disable",
                "??5??????   /lib/netplan/00-network-manager-all.yaml",
                "??5??????   /var/lib/rkhunter/db/mirrors.dat",
            ]
        ),
        dpkg_rc=0,
    )

    assert result["risk"] == "low"
    assert result["review"] == []
    assert {item["code"] for item in result["expected"]} == {"dpkg_expected_noise"}
    assert result["propupd_allowed"] is True


def test_unverified_replaced_script_warning_still_requires_review():
    result = analyze_rkhunter_output(
        _complete_scan(
            "Warning: The command '/usr/bin/example' has been replaced by a script"
        ),
        1,
        dpkg_output="",
        dpkg_rc=0,
        dpkg_owner_output="/usr/bin/example\t1\tdpkg-query: no path found matching pattern",
        file_type_output="/usr/bin/example\t0\tPOSIX shell script, ASCII text executable",
    )

    assert result["risk"] == "medium"
    assert result["review"][0]["code"] == "unclassified_warning"
    assert result["propupd_allowed"] is False


def test_propupd_requires_complete_scan_and_successful_dpkg_verification():
    incomplete = analyze_rkhunter_output("No warnings", 0, dpkg_rc=0)
    failed_dpkg = analyze_rkhunter_output(
        _complete_scan(),
        0,
        dpkg_rc=2,
    )

    assert incomplete["propupd_allowed"] is False
    assert failed_dpkg["propupd_allowed"] is False
