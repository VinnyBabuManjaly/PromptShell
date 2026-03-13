"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import yaml

from prompt_shell.config import AppConfig, load_config


def test_default_config():
    config = AppConfig()
    assert config.terminal.backend == "auto"
    assert config.voice.engine == "whisper_local"
    assert config.llm.provider == "ollama"
    assert config.delivery.method == "clipboard"


def test_load_config_from_yaml():
    data = {
        "terminal": {"backend": "tmux", "screen_buffer_lines": 50},
        "voice": {"engine": "whisper_api", "whisper_model": "small.en"},
        "llm": {"provider": "openai", "model": "gpt-4o-mini", "api_key": "${OPENAI_API_KEY}"},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        tmp_path = Path(f.name)

    try:
        config = load_config(tmp_path)
        assert config.terminal.backend == "tmux"
        assert config.terminal.screen_buffer_lines == 50
        assert config.voice.engine == "whisper_api"
        assert config.voice.whisper_model == "small.en"
        assert config.llm.provider == "openai"
    finally:
        tmp_path.unlink()


def test_load_config_iterm2_backend():
    data = {"terminal": {"backend": "iterm2"}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        tmp_path = Path(f.name)

    try:
        config = load_config(tmp_path)
        assert config.terminal.backend == "iterm2"
    finally:
        tmp_path.unlink()


def test_load_config_generic_backend():
    data = {"terminal": {"backend": "generic"}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        tmp_path = Path(f.name)

    try:
        config = load_config(tmp_path)
        assert config.terminal.backend == "generic"
    finally:
        tmp_path.unlink()


def test_resolve_api_key_env_var(monkeypatch):
    config = AppConfig()
    config.llm.api_key = "${MY_TEST_KEY}"
    monkeypatch.setenv("MY_TEST_KEY", "sk-test-12345")
    assert config.llm.resolve_api_key() == "sk-test-12345"


def test_resolve_api_key_literal():
    config = AppConfig()
    config.llm.api_key = "sk-literal-key"
    assert config.llm.resolve_api_key() == "sk-literal-key"


def test_load_nonexistent_config():
    config = load_config(Path("/tmp/does_not_exist_prompt_shell.yaml"))
    # Should fall back to defaults
    assert config.terminal.backend == "auto"


def test_gemini_provider_accepted():
    from prompt_shell.config import LLMConfig

    config = LLMConfig(
        provider="gemini",
        model="gemini-2.0-flash",
        cloud_run_url="https://prompt-shell-abc123-uc.a.run.app",
    )
    assert config.provider == "gemini"
    assert config.cloud_run_url == "https://prompt-shell-abc123-uc.a.run.app"


def test_cloud_run_url_env_var_resolution(monkeypatch):
    from prompt_shell.config import LLMConfig

    monkeypatch.setenv("CLOUD_RUN_URL", "https://my-service-xyz.a.run.app")
    config = LLMConfig(
        provider="gemini", model="gemini-2.0-flash", cloud_run_url="${CLOUD_RUN_URL}"
    )
    assert config.resolve_cloud_run_url() == "https://my-service-xyz.a.run.app"


def test_cloud_run_url_literal():
    from prompt_shell.config import LLMConfig

    config = LLMConfig(provider="gemini", cloud_run_url="https://literal-url.a.run.app")
    assert config.resolve_cloud_run_url() == "https://literal-url.a.run.app"


def test_cloud_run_url_none():
    from prompt_shell.config import LLMConfig

    config = LLMConfig(provider="gemini", cloud_run_url=None)
    assert config.resolve_cloud_run_url() is None
