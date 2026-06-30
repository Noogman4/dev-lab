import base64

import pytest

from netmon.services.ai_online_service import AiOnlineService


def test_analyze_returns_only_api_error_message():
    service = AiOnlineService()
    service.api_key = "demo"
    service._post_json = lambda *_args, **_kwargs: (
        429,
        (
            '{"error":{"message":"You exceeded your current quota, '
            'please check your plan and billing details.",'
            '"type":"insufficient_quota","param":null,"code":"insufficient_quota"}}'
        ),
    )

    success, result = service.analyze("demo prompt")

    assert success is False
    assert (
        result
        == "Fehler: You exceeded your current quota, please check your plan and billing details."
    )


def test_chat_returns_unknown_api_error_when_parsing_fails():
    service = AiOnlineService()
    service.api_key = "demo"
    service._post_json = lambda *_args, **_kwargs: (500, "<html>bad gateway</html>")

    success, result = service.chat([{"role": "user", "content": "Hallo"}])

    assert success is False
    assert result == "Fehler: Unbekannter API-Fehler"


def test_analyze_tracks_token_usage_from_response():
    service = AiOnlineService()
    service.api_key = "demo"
    service._post_json = lambda *_args, **_kwargs: (
        200,
        '{"output_text":"ok","usage":{"input_tokens":12,"output_tokens":8,"total_tokens":20}}',
    )

    success, result = service.analyze("demo prompt")

    assert success is True
    assert result == "ok"
    assert service.last_usage == {
        "input_tokens": 12,
        "output_tokens": 8,
        "total_tokens": 20,
    }
    assert service.last_usage_text == "Gesamt: 20 | Input: 12 | Output: 8"


def test_image_to_data_url_accepts_image_inside_home(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    image_path = tmp_path / "demo.png"
    image_path.write_bytes(b"png-bytes")

    result = AiOnlineService().image_to_data_url(str(image_path))

    assert result == f"data:image/png;base64,{base64.b64encode(b'png-bytes').decode('ascii')}"


def test_image_to_data_url_rejects_path_outside_home(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    outside_dir = tmp_path / "outside"
    home_dir.mkdir()
    outside_dir.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    image_path = outside_dir / "demo.png"
    image_path.write_bytes(b"png-bytes")

    with pytest.raises(ValueError, match="inside the user home directory"):
        AiOnlineService().image_to_data_url(str(image_path))
