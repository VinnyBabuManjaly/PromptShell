"""Tests for file delivery method."""

import tempfile
from pathlib import Path

from prompt_shell.config import DeliveryConfig
from prompt_shell.delivery.file import deliver_to_file


async def test_delivers_prompt_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "last_prompt.txt"
        result = await deliver_to_file("Fix the import error", output_path)
        assert result is True
        assert output_path.read_text(encoding="utf-8") == "Fix the import error"


async def test_creates_parent_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "nested" / "dir" / "prompt.txt"
        result = await deliver_to_file("some prompt", output_path)
        assert result is True
        assert output_path.exists()


async def test_overwrites_existing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "prompt.txt"
        output_path.write_text("old content", encoding="utf-8")
        await deliver_to_file("new prompt", output_path)
        assert output_path.read_text(encoding="utf-8") == "new prompt"


def test_delivery_config_default_output_file():
    config = DeliveryConfig(method="file")
    assert config.output_file == Path.home() / ".prompt-shell" / "last_prompt.txt"


def test_delivery_config_custom_output_file():
    config = DeliveryConfig(method="file", output_file=Path("/tmp/my_prompt.txt"))
    assert config.output_file == Path("/tmp/my_prompt.txt")


def test_file_method_accepted_in_app_config():
    import tempfile

    import yaml

    data = {"delivery": {"method": "file", "output_file": "/tmp/prompt.txt"}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        tmp_path = Path(f.name)

    try:
        from prompt_shell.config import load_config

        config = load_config(tmp_path)
        assert config.delivery.method == "file"
        assert config.delivery.output_file == Path("/tmp/prompt.txt")
    finally:
        tmp_path.unlink()
