from pathlib import Path

import pytest

from app.core import ai_config as ai_config_module


@pytest.fixture(autouse=True)
def _force_demo_config(monkeypatch: pytest.MonkeyPatch) -> None:
    demo_path = Path(__file__).resolve().parents[3] / "config" / "llm.config.demo.json"
    monkeypatch.setattr(ai_config_module, "get_ai_config_path", lambda: demo_path)


def test_load_demo_ai_config() -> None:
    config = ai_config_module.load_ai_config()

    assert config.active_provider == "mock"
    assert config.active_llm.default_model == "mock"
    assert config.embedding.provider == "local"
    assert config.agent.runtime in {"ledgerline", "pi_coding_agent"}