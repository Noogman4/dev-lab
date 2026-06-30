from netmon.services.ai_analysis_service import AiAnalysisService


def test_path_guard_prompt_adds_cautious_focus():
    service = AiAnalysisService()

    prompt = service.build_prompt(
        "PATH Guard Analyse",
        'PATH enthält /tmp und export PATH="/tmp:$PATH"',
    )

    assert "PATH-Manipulationen" in prompt
    assert "/tmp, /var/tmp, /dev/shm, '.', $PWD" in prompt
    assert "Behaupte nicht, dass Malware sicher vorhanden ist." in prompt
